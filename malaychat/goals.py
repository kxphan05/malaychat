"""Goal management: creation, tracking, and completion detection."""

import re
import streamlit as st


def init_goals() -> None:
    """Initialize goal state in session."""
    if "goals" not in st.session_state:
        st.session_state.goals = []


def add_goal(text: str) -> None:
    """Add a new learning goal."""
    if text.strip():
        st.session_state.goals.append({"text": text.strip(), "completed": False})


def remove_goal(index: int) -> None:
    """Remove a goal by index."""
    if 0 <= index < len(st.session_state.goals):
        st.session_state.goals.pop(index)


def toggle_goal(index: int) -> None:
    """Manually toggle goal completion."""
    if 0 <= index < len(st.session_state.goals):
        st.session_state.goals[index]["completed"] = not st.session_state.goals[index]["completed"]


def check_goal_completion(response: str) -> list[int]:
    """
    Detect if any active goals have been addressed in the assistant response.

    Uses keyword matching: if key words from a goal appear in the response,
    the goal is considered completed. Returns indices of newly completed goals.
    """
    newly_completed = []
    for i, goal in enumerate(st.session_state.goals):
        if goal["completed"]:
            continue

        # Extract meaningful keywords (3+ chars) from the goal
        keywords = [
            w.lower()
            for w in re.findall(r"\b\w+\b", goal["text"])
            if len(w) >= 3 and w.lower() not in _STOP_WORDS
        ]

        if not keywords:
            continue

        response_lower = response.lower()
        matched = sum(1 for kw in keywords if kw in response_lower)
        # Complete if majority of keywords found
        if matched >= max(1, len(keywords) // 2):
            st.session_state.goals[i]["completed"] = True
            newly_completed.append(i)

    return newly_completed


def get_goals() -> list[dict]:
    """Return the current goals list."""
    return st.session_state.goals


_STOP_WORDS = {
    "the", "and", "for", "how", "can", "learn", "want", "use",
    "some", "few", "about", "with", "that", "this", "from",
    "will", "should", "would", "could", "have", "has", "are",
    "was", "were", "been", "being", "what", "when", "where",
    "which", "who", "whom", "why", "does", "did", "doing",
    "each", "every", "all", "any", "most", "other", "into",
}
