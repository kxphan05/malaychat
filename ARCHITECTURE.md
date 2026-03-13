# MalayChat Architecture

## Overview

MalayChat is a Malay language learning app using a **two-model architecture with tool calling**:
- **Molmo2-8B** (`allenai/Molmo2-8B`) — LLM via PublicAI Inference API (no local GPU needed)
- **mesolitica/nanot5-base-malaysian-translation-v2.1** — runs locally (~300MB), wrapped as tool objects (`translate_to_malay`, `translate_to_english`)

A pattern-based router decides when to invoke translation tools. Tool results are injected into the LLM's system prompt, so the LLM uses verified translations rather than guessing. Tool calls are visible in the UI via `st.status` widgets.

Users authenticate with a simple username/password system. Progress (completed lessons, vocabulary, streaks) is persisted to Google Sheets so it survives Streamlit Cloud restarts.

## Directory Structure

```
tutor/
├── main.py              # Entry point — run with `streamlit run main.py`
├── pyproject.toml       # Project config and dependencies (managed by uv)
├── packages.txt         # System dependencies for Streamlit Cloud
├── .streamlit/
│   └── secrets.toml.example  # Template for all required secrets
├── prd.md               # Product requirements document
├── malaychat/
│   ├── __init__.py
│   ├── auth.py          # Username/password authentication via Google Sheets
│   ├── chat.py          # Streamlit UI: login gate, chat interface, sidebar, lesson panel
│   ├── model.py         # Orchestrator: routes tools then streams LLM
│   ├── tools.py         # Tool definitions + pattern-based routing logic
│   ├── llm.py           # Molmo2-8B via PublicAI Inference API with streaming
│   ├── translator.py    # nanot5 translation (runs locally, consumed by tools.py)
│   ├── goals.py         # Goal CRUD and completion detection
│   ├── prompts.py       # Recommended prompts engine (goal-aware + lesson-aware)
│   ├── curriculum.py    # Structured curriculum: 3 levels, 11 lessons with vocabulary
│   └── progress.py      # Progress persistence via Google Sheets (per-user)
├── ARCHITECTURE.md      # This file
├── PROGRESS.md          # Implementation progress tracker
└── PAST_MISTAKES.md     # Lessons learned and bugs encountered
```

> **Note:** The package was originally named `app/` but was renamed to `malaychat/` to avoid a namespace collision with Streamlit's internal `app` module, which caused `KeyError: 'app.goals'` on Streamlit Cloud.

## Module Responsibilities

### `malaychat/auth.py` — Authentication
- Simple username/password login using a `users` worksheet tab in the Google Sheet
- Passwords stored as SHA-256 hashes
- `render_login()` — shows a login/register form with tabs; returns username if authenticated, `None` otherwise
- `authenticate(username, password)` / `register(username, password)` — check/create credentials
- Login gate in `chat.py`: `render_login()` is called first; if it returns `None`, the rest of the app doesn't render
- Logout clears all session state and reruns

### `malaychat/tools.py` — Tool Definitions & Router
- Defines `Tool` and `ToolOutput` dataclasses (lightweight replacements for LlamaIndex `FunctionTool`)
- `translate_to_malay_tool` and `translate_to_english_tool` wrap the nanot5 translator
- `route_and_call_tools(user_message)` uses regex patterns to detect when translation is needed
- `_extract_phrase()` pulls out the specific phrase to translate (handles quoted text, "how do I say X", etc.)

### `malaychat/model.py` — Orchestrator
- `get_tool_results()` — calls `route_and_call_tools()`, returned separately so chat.py can display tool calls before streaming
- `stream_response()` — formats `ToolOutput` results into context string and passes to LLM, along with `active_lesson_id`

### `malaychat/llm.py` — Molmo2-8B (PublicAI Inference API)
- Uses `requests` to call PublicAI's OpenAI-compatible endpoint (`https://api.publicai.co/v1/chat/completions`)
- Model: `allenai/Molmo2-8B`
- SSE streaming with `max_tokens=1024`
- Parses both `content` and `reasoning_content` delta fields
- Repetition detection (`_is_repeating()`) to stop runaway generation (tuned for breakdown format: `min_length=250`, `window=80`, phrase check starts at length 30)
- Reads `PUBLICAI_API_KEY` from Streamlit secrets
- **Three system prompt modes** (structured for an 8B model — flat, explicit, with examples):
  - `LEARNING_SYSTEM_PROMPT`: translation requests get phrase + example + word-by-word breakdown; conversation/practice requests trigger role-play engagement
  - `CHAT_SYSTEM_PROMPT`: freeform conversation with Malay sentences always broken down word by word
  - `ROLEPLAY_SYSTEM_PROMPT`: **replaces** (not appends to) the base prompt when role-play is active — instructs the model to stay in character, only break down its own replies, never explain the user's messages
- **Active lesson injection**: when a lesson is active, the lesson title, description, and vocabulary are appended to the system prompt so the LLM focuses on the right words
- **Breakdown format** for every Malay sentence: `**Malay sentence.** / Breakdown: *word1* (meaning) + *word2* (meaning) / Meaning: "English translation"`

### `malaychat/translator.py` — nanot5 (Local Translation)
- Loads `mesolitica/nanot5-base-malaysian-translation-v2.1` locally (~300MB)
- `to_malay(text)` / `to_english(text)` — consumed by the tools in `tools.py`
- Cached with `@st.cache_resource` so the model loads only once

### `malaychat/goals.py` — Goal Management
- Goals in `st.session_state.goals` as `[{"text": str, "completed": bool}]`
- Keyword-based completion detection on assistant responses (with stop-word filtering)
- Active goals are injected into the LLM system prompt in Learning Mode

### `malaychat/curriculum.py` — Structured Curriculum
- **3 levels, 11 lessons**: Foundations (greetings, numbers, polite expressions) → Daily Life (food, shopping, directions, transport) → Conversations (family, weather, hotel, emergencies)
- Each lesson contains: `id`, `title`, `description`, `vocabulary` (8-12 items with Malay/English pairs), `practice_prompts` (3-5 per lesson), `completion_criteria` (vocab practiced + messages exchanged)
- Flat lookup index (`_LESSON_INDEX`) for O(1) lesson access by ID
- `ALL_LESSON_IDS` ordered list for sequential navigation
- `get_next_lesson(current_id, completed)` — finds next uncompleted lesson
- `format_vocab_reference(lesson_id)` — formats vocabulary as a markdown reference card

### `malaychat/progress.py` — Progress Persistence (Google Sheets)
- Uses `gspread` + Google service account to read/write a Google Sheet as a key-value store
- **Data stored**: `current_lesson`, `completed_lessons`, `vocabulary` (word → times_seen, first/last seen), `sessions` (date, lesson, messages, vocab practiced), `stats` (streaks, totals)
- Sheet is auto-initialized with defaults on first load (`_init_sheet()`)
- `extract_vocabulary(response, lesson_vocab)` — detects which lesson vocab items appear in assistant responses (checks bold markdown and plain text)
- `get_lesson_progress(progress, lesson_id)` — returns current vocab/message counts vs requirements for a lesson
- `check_lesson_completion(progress, lesson_id)` — delegates to `get_lesson_progress()` and checks if both criteria are met
- `complete_lesson()` / `record_vocab()` / `record_session()` — high-level operations that mutate progress and save to sheet
- Streak calculation: tracks consecutive days with at least one session
- **Multi-user**: each user gets their own worksheet tab (`progress_{username}`), so progress is isolated
- Cached gspread client via `@st.cache_resource` to avoid re-authenticating on every rerun

### `malaychat/prompts.py` — Recommended Prompts Engine
- Generates contextual prompt suggestions based on goals, conversation history, mode, and active lesson
- **Lesson-aware**: when a lesson is active, suggests lesson-specific `practice_prompts` instead of generic category prompts
- **12 topic categories**: greetings, food, marketplace, numbers, directions, transport, polite expressions, weather, family, time, hotel, emergency — each with keyword mappings and 3-5 curated prompts
- **Goal classification**: matches goal text to categories via keyword analysis (`_classify_goal()`)
- **Follow-up detection**: analyzes recent messages to suggest relevant next steps (`_detect_recent_topics()`)
- **Deduplication**: skips prompts similar to what the user already asked (60% word overlap threshold via `_already_asked()`)
- **Mode-aware**: Learning mode suggests goal-aligned prompts; Chat mode suggests freeform conversation starters
- Returns up to 3 suggestions via `get_recommended_prompts(goals, messages, mode, active_lesson_id)`

### `malaychat/chat.py` — Streamlit Interface
- **Login gate**: `render_login()` called first — blocks the app until authenticated
- **Sidebar**:
  - Username display + logout button
  - Mode toggle (Learning/Chat)
  - Lesson panel (Learning mode): expandable levels with lesson list, active lesson indicator, lesson progress bars (Vocab: X/Y, Messages: X/Y), vocabulary reference card, "Complete Lesson" button, navigation (Previous/Next/Exit)
  - Goal management: add/remove goals, completion indicators
  - Progress dashboard: streak counter, level progress bars, vocab/session metrics, vocabulary journal expander
  - Clear chat button
- **Chat area**:
  - Lesson-aware welcome message (introduces lesson topic when active)
  - Message history rendering
  - Role-play toggle (right-aligned, above recommended prompts)
  - Recommended prompt buttons (up to 3, lesson-aware)
  - Chat input
  - Tool call visibility via `st.status` widgets
  - `st.write_stream()` for token-by-token display
- **Post-response hooks** (run after every assistant response):
  - Goal completion detection (Learning mode)
  - Vocabulary extraction from response (when lesson active)
  - Session recording to Google Sheets
  - Lesson completion check (auto-advance with balloons + toast)
  - `st.rerun()` to refresh recommended prompts

## Data Flow

```
User opens app
    │
    ▼
┌──────────────┐
│  auth.py     │  ← render_login() — blocks until authenticated
└──────┬───────┘
       │ username
       ▼
┌──────────────┐
│  progress.py │  ← load_progress() from Google Sheets (user-specific tab)
└──────┬───────┘
       │ progress dict → session state
       ▼
┌──────────────────────────────────────────────┐
│  chat.py — main loop                         │
│                                              │
│  User Input ("How do I say thank you?")      │
│      │                                       │
│      ▼                                       │
│  ┌──────────┐                                │
│  │ model.py │ ← get_tool_results()           │
│  └────┬─────┘                                │
│       │                                      │
│       ▼                                      │
│  ┌──────────┐    pattern match → needs translation
│  │ tools.py │──▶ translate_to_malay("thank you")
│  └────┬─────┘         │                      │
│       │               ▼                      │
│       │         ┌──────────────┐             │
│       │         │ translator.py│ → "terima kasih"
│       │         └──────────────┘             │
│       │                                      │
│       ▼                                      │
│  st.status widget shows tool call + result   │
│       │                                      │
│       ▼                                      │
│  ┌──────────┐    system prompt + tool results│
│  │ model.py │ ← stream_response()            │
│  └────┬─────┘    + active lesson context     │
│       │                                      │
│       ▼                                      │
│  ┌──────────┐                                │
│  │  llm.py  │──▶ streamed tokens             │
│  └──────────┘    → st.write_stream()         │
│       │                                      │
│       ▼                                      │
│  Post-response hooks:                        │
│  ├─ goals.py    ← check goal completion      │
│  ├─ progress.py ← extract vocab, record session
│  └─ progress.py ← check lesson completion    │
│       │                                      │
│       ▼                                      │
│  st.rerun() → refresh prompts               │
└──────────────────────────────────────────────┘
```

## Key Design Decisions

1. **PublicAI Inference API for LLM**: No local GPU/memory needed, deploys on Streamlit Cloud within 1GB RAM. Uses Molmo2-8B via PublicAI's OpenAI-compatible endpoint.
2. **Local translator**: nanot5 is small (~300MB) and runs locally for fast, reliable translations without additional API latency.
3. **Pattern-based tool routing**: Regex patterns detect when translation is needed. Small models can't reliably do structured ReAct-style tool calling, so pattern matching is more robust.
4. **Selective tool use**: Only translation-related queries trigger tool calls. General conversation goes directly to the LLM.
5. **Visible tool calls**: Tool calls are shown in the UI via `st.status` widgets before the LLM response streams, so users can see what translation happened.
6. **SSE streaming**: Both `content` and `reasoning_content` delta fields are parsed from the SSE stream, ensuring responses are never empty.
7. **Package naming**: `malaychat/` instead of `app/` to avoid Streamlit's internal namespace collision.
8. **Streaming with safety**: Token streaming with repetition detection to catch and stop runaway generation loops. Thresholds are tuned to avoid false positives from the word-by-word breakdown format.
9. **Word-by-word breakdowns**: Every Malay example sentence is broken down into individual words with meanings, helping learners understand sentence structure rather than just memorizing phrases.
10. **Roleplay as prompt replacement**: Small models can't handle conflicting instructions (e.g., "always break down every Malay sentence" vs "don't translate the user's messages"). The roleplay prompt **replaces** the base prompt entirely rather than appending, eliminating the conflict.
11. **Goal-aware prompt suggestions**: Recommended prompts are generated dynamically based on active goals, conversation history, and mode. Prompts that have already been asked are filtered out to keep suggestions fresh.
12. **Structured curriculum as Python data**: The curriculum (3 levels, 11 lessons, ~120 vocabulary items) is stored as plain Python dicts — no database, no external files. This keeps deployment simple (no migration/loading step) and makes the curriculum easy to edit. Lesson vocabulary is injected into the LLM system prompt so the model focuses on teaching the right words.
13. **Google Sheets for persistence**: Streamlit Cloud's filesystem is ephemeral — files are lost on restart/redeploy. Google Sheets was chosen over localStorage (single-device) and Supabase (overkill). A single spreadsheet holds both user credentials and per-user progress in separate worksheet tabs.
14. **Per-user worksheet tabs**: Each user's progress lives in its own worksheet tab (`progress_{username}`), providing data isolation without needing a real database. The `users` tab stores credentials.
15. **Dual lesson completion**: Lessons can auto-complete (when vocab + message criteria are met) or be manually completed via a button. Users can see their progress toward criteria via progress bars in the sidebar. This gives users agency — they decide when they've learned enough.
16. **`st.rerun()` after every response**: Without this, recommended prompts showed stale suggestions because they were computed before the new messages were added to history. The rerun ensures prompts always reflect the latest conversation state.
