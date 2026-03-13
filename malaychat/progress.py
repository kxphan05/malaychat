"""Progress tracking with Google Sheets as persistent storage."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

from malaychat.curriculum import get_lesson, get_next_lesson

logger = logging.getLogger("malaychat.progress")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet layout: a single worksheet with key-value rows
# Row 1: header ("key", "value")
# Row 2: ("current_lesson", "1.1")
# Row 3: ("completed_lessons", '["1.1","1.2"]')    — JSON-encoded
# Row 4: ("vocabulary", '{...}')                     — JSON-encoded
# Row 5: ("sessions", '[...]')                       — JSON-encoded
# Row 6: ("stats", '{...}')                          — JSON-encoded
_KEYS = ["current_lesson", "completed_lessons", "vocabulary", "sessions", "stats"]

_DEFAULT_PROGRESS = {
    "current_lesson": "1.1",
    "completed_lessons": [],
    "vocabulary": {},
    "sessions": [],
    "stats": {
        "total_sessions": 0,
        "total_messages": 0,
        "total_vocab_learned": 0,
        "current_streak_days": 0,
        "longest_streak_days": 0,
        "last_session_date": "",
    },
}


@st.cache_resource
def _get_client() -> gspread.Client:
    """Create an authenticated gspread client from Streamlit secrets."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_worksheet() -> gspread.Worksheet:
    """Open the progress spreadsheet and return the first worksheet."""
    client = _get_client()
    spreadsheet_url = st.secrets.get("PROGRESS_SHEET_URL", "")
    if not spreadsheet_url:
        raise ValueError(
            "PROGRESS_SHEET_URL not set in Streamlit secrets. "
            "Create a Google Sheet and add its URL to secrets."
        )
    spreadsheet = client.open_by_url(spreadsheet_url)
    return spreadsheet.sheet1


def _init_sheet(ws: gspread.Worksheet) -> None:
    """Initialize the sheet with headers and default values if empty."""
    existing = ws.get_all_values()
    if existing:
        return

    rows = [["key", "value"]]
    for key in _KEYS:
        val = _DEFAULT_PROGRESS[key]
        rows.append([key, val if isinstance(val, str) else json.dumps(val)])
    ws.update(range_name="A1", values=rows)
    logger.info("Initialized progress sheet with defaults")


def load_progress() -> dict:
    """Load progress from Google Sheets. Returns a progress dict."""
    try:
        ws = _get_worksheet()
        _init_sheet(ws)
        rows = ws.get_all_values()
    except Exception:
        logger.exception("Failed to load progress from Google Sheets")
        return _default_progress_copy()

    data = {}
    for row in rows[1:]:  # skip header
        if len(row) < 2:
            continue
        key, val = row[0], row[1]
        if key in ("completed_lessons", "vocabulary", "sessions", "stats"):
            try:
                data[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                data[key] = _DEFAULT_PROGRESS[key]
        elif key == "current_lesson":
            data[key] = val or "1.1"

    # Fill in any missing keys
    for key in _KEYS:
        if key not in data:
            data[key] = _DEFAULT_PROGRESS[key]

    return data


def save_progress(progress: dict) -> None:
    """Save progress dict to Google Sheets."""
    try:
        ws = _get_worksheet()
        rows = [["key", "value"]]
        for key in _KEYS:
            val = progress.get(key, _DEFAULT_PROGRESS[key])
            rows.append([key, val if isinstance(val, str) else json.dumps(val)])
        ws.update(range_name="A1", values=rows)
    except Exception:
        logger.exception("Failed to save progress to Google Sheets")


def _default_progress_copy() -> dict:
    """Return a fresh copy of default progress."""
    return json.loads(json.dumps(_DEFAULT_PROGRESS))


# --- High-level operations ---


def complete_lesson(progress: dict, lesson_id: str) -> None:
    """Mark a lesson as completed and advance to the next one."""
    if lesson_id not in progress["completed_lessons"]:
        progress["completed_lessons"].append(lesson_id)
    next_id = get_next_lesson(lesson_id, progress["completed_lessons"])
    if next_id:
        progress["current_lesson"] = next_id
    save_progress(progress)


def record_vocab(progress: dict, word: str, english: str, lesson_id: str) -> None:
    """Record a vocabulary item as practiced."""
    today = date.today().isoformat()
    vocab = progress["vocabulary"]
    if word in vocab:
        vocab[word]["times_seen"] += 1
        vocab[word]["last_seen"] = today
    else:
        vocab[word] = {
            "english": english,
            "lesson_id": lesson_id,
            "times_seen": 1,
            "first_seen": today,
            "last_seen": today,
        }


def record_session(
    progress: dict,
    lesson_id: str | None,
    messages_count: int,
    vocab_practiced: list[str],
) -> None:
    """Record a session and update stats."""
    today = date.today().isoformat()
    progress["sessions"].append({
        "date": today,
        "lesson_id": lesson_id or "",
        "messages_count": messages_count,
        "vocab_practiced": vocab_practiced,
    })

    stats = progress["stats"]
    stats["total_sessions"] += 1
    stats["total_messages"] += messages_count
    stats["total_vocab_learned"] = len(progress["vocabulary"])

    # Update streak
    last_date = stats.get("last_session_date", "")
    if last_date:
        try:
            last = datetime.strptime(last_date, "%Y-%m-%d").date()
            diff = (date.today() - last).days
            if diff == 1:
                stats["current_streak_days"] += 1
            elif diff > 1:
                stats["current_streak_days"] = 1
            # diff == 0: same day, streak unchanged
        except ValueError:
            stats["current_streak_days"] = 1
    else:
        stats["current_streak_days"] = 1

    stats["longest_streak_days"] = max(
        stats["longest_streak_days"], stats["current_streak_days"]
    )
    stats["last_session_date"] = today
    save_progress(progress)


def get_level_progress(progress: dict, level_num: int) -> tuple[int, int]:
    """Return (completed, total) lessons for a level."""
    from malaychat.curriculum import get_all_levels

    for level in get_all_levels():
        if level["level"] == level_num:
            total = len(level["lessons"])
            done = sum(
                1 for l in level["lessons"]
                if l["id"] in progress["completed_lessons"]
            )
            return done, total
    return 0, 0


# --- Vocabulary detection ---


def extract_vocabulary(response: str, lesson_vocab: list[dict]) -> list[str]:
    """
    Check which lesson vocabulary items appear in the assistant's response.

    Looks for Malay words/phrases in the response text — checks both the bold
    markdown pattern (**word**) and plain text occurrence.
    """
    found = []
    response_lower = response.lower()
    for item in lesson_vocab:
        malay = item["malay"]
        malay_lower = malay.lower()
        # Check bold markdown pattern: **word**
        if f"**{malay}" in response or f"**{malay.lower()}" in response.lower():
            found.append(malay)
        # Check plain text occurrence (for multi-word phrases)
        elif malay_lower in response_lower:
            found.append(malay)
    return found


def check_lesson_completion(progress: dict, lesson_id: str) -> bool:
    """Check if a lesson's completion criteria have been met."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        return False
    criteria = lesson["completion_criteria"]

    # Gather all vocab practiced and messages in sessions for this lesson
    lesson_sessions = [s for s in progress["sessions"] if s["lesson_id"] == lesson_id]
    all_vocab: set[str] = set()
    total_messages = 0
    for session in lesson_sessions:
        all_vocab.update(session.get("vocab_practiced", []))
        total_messages += session.get("messages_count", 0)

    return (
        len(all_vocab) >= criteria["vocab_practiced"]
        and total_messages >= criteria["messages_exchanged"]
    )


def reset_progress() -> dict:
    """Reset all progress to defaults and save."""
    progress = _default_progress_copy()
    save_progress(progress)
    return progress
