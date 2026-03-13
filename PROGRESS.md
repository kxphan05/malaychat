# MalayChat Progress

## Phase 1: MVP Foundation — COMPLETE

### Week 1-2: Model Integration
- [x] Set up project with `uv` package manager (Python 3.13)
- [x] Dependencies: streamlit, transformers, torch, sentencepiece, requests
- [x] **Two-model architecture with tool calling**:
  - `malaychat/llm.py` — Molmo2-8B (`allenai/Molmo2-8B`) via PublicAI Inference API
  - `malaychat/translator.py` — nanot5 translation model runs locally (~300MB)
  - `malaychat/tools.py` — Tool definitions (`Tool`/`ToolOutput` dataclasses) + pattern-based routing
  - `malaychat/model.py` — Orchestrator: routes tools → injects results → streams LLM
- [x] PublicAI Inference API streaming via SSE (`requests.post` with `stream=True`)
- [x] Supports both `content` and `reasoning_content` delta fields, `max_tokens=1024`
- [x] Repetition detection (streaming-side loop detector)
- [x] Comprehensive logging throughout the pipeline
- [x] Deployable on Streamlit Cloud (no C compiler needed, fits in 1GB RAM)

### Week 3: Streamlit Chat Interface
- [x] Built `malaychat/chat.py` with full chat UI
- [x] Mode toggle: Learning Mode (structured practice) and Chat Mode (freeform)
- [x] Chat message history with Streamlit's `st.chat_message`
- [x] Token-by-token streaming display via `st.write_stream()`
- [x] **Tool call visibility**: `st.status` widgets show tool name, input phrase, and translation result before the LLM response streams
- [x] Welcome message with usage instructions
- [x] Clear chat button

### Week 4: Goal Sidebar
- [x] Goal sidebar in `malaychat/goals.py` with add/remove functionality
- [x] Visual completion indicators (checkmark vs empty box)
- [x] Automatic goal completion detection via keyword matching in responses
- [x] Toast notifications on goal completion
- [x] Goals counter metric in sidebar
- [x] Empty state with suggested starter goals
- [x] Goals injected into system prompt so model works toward them

### Deployment & Fixes
- [x] Renamed `app/` to `malaychat/` to fix Streamlit Cloud namespace collision (`KeyError: 'app.goals'`)
- [x] `packages.txt` for Streamlit Cloud system dependencies (build-essential, cmake, clang)
- [x] `.streamlit/secrets.toml.example` for PUBLICAI_API_KEY configuration
- [x] Iterated through multiple LLM approaches before settling on Molmo2-8B via PublicAI:
  - mallam-3B → SeaLLMs → Llama 3.2 (various quantizations) → HF Inference API → DeepSeek R1 → Apriel 1.6 15B Thinker → Molmo2-8B (PublicAI)
- [x] Replaced LlamaIndex ReAct tool calling with pattern-based routing (small models can't do structured ReAct)
- [x] Replaced LlamaIndex `FunctionTool` with custom lightweight `Tool`/`ToolOutput` dataclasses

### Deliverable
Working prototype deployed to Streamlit Cloud.

Run locally:
```bash
uv run streamlit run main.py
```

Deploy to Streamlit Cloud:
1. Push to GitHub
2. Add `PUBLICAI_API_KEY` in Streamlit Cloud Settings > Secrets

### Phase 1.5: Prompt System & Role-play
- [x] **Recommended prompts system** (`malaychat/prompts.py`):
  - 12 topic categories (greetings, food, marketplace, numbers, directions, transport, polite, weather, family, time, hotel, emergency) with curated prompts per category
  - Goal-aware: classifies active goals into categories and suggests matching prompts
  - Follow-up detection: analyzes recent messages to suggest relevant next steps
  - Deduplication: filters out prompts similar to what was already asked (60% word overlap)
  - Mode-aware: Learning mode = goal-aligned, Chat mode = freeform conversation starters
  - Displayed as up to 3 clickable buttons below the chat history
- [x] **Word-by-word sentence breakdowns**:
  - System prompts updated to require breakdown of every Malay example sentence
  - Format: `**Malay sentence** / Breakdown: *word* (meaning) + ... / Meaning: "English"`
  - Prompts simplified to flat structure for 8B model comprehension (no nested bullets)
  - Repetition detection thresholds relaxed (`min_length=250`, phrase check starts at 30) to avoid false positives from breakdown format
- [x] **Role-play toggle**:
  - Toggle switch in the chat area (`st.toggle`)
  - When active, appends `ROLEPLAY_CONTEXT` to system prompt with explicit stay-in-character instructions
  - Caption updates to show "(Role-play active)"
  - Flows through `chat.py` → `model.py` → `llm.py` → system prompt

---

## Phase 2: Core Experience — IN PROGRESS

- [x] ~~Auto-goal suggestions based on conversation context~~ (done in Phase 1.5 as recommended prompts)

### Problem Statement

Two interrelated gaps in the current experience:

1. **No fixed learning template**: Users have no structured path — they set ad-hoc goals and get ad-hoc prompts, but there's no curriculum guiding them through Malay in a logical order. A beginner doesn't know *what* to learn or *in what order*.
2. **No progress tracking**: Everything lives in `st.session_state` and is lost on page refresh. Users can't see what they've learned, which lessons they've completed, or what vocabulary they've collected across sessions.

These are interrelated because a structured curriculum defines what "progress" means (which lessons, which vocabulary), and progress tracking shows where the user is within that curriculum.

---

### Feature A: Structured Learning Template (Curriculum)

**New module: `malaychat/curriculum.py`**

A structured curriculum of levels and lessons, stored as Python data structures (no database needed). Each lesson is a self-contained learning unit with clear objectives and completion criteria.

#### Curriculum Structure

```python
CURRICULUM = [
    {
        "level": 1,
        "title": "Foundations",
        "lessons": [
            {
                "id": "1.1",
                "title": "Greetings & Introductions",
                "description": "Learn to greet people and introduce yourself",
                "vocabulary": [
                    {"malay": "Selamat pagi", "english": "Good morning"},
                    {"malay": "Apa khabar?", "english": "How are you?"},
                    {"malay": "Nama saya...", "english": "My name is..."},
                    # ... 8-12 words/phrases per lesson
                ],
                "practice_prompts": [
                    "Teach me how to greet someone in the morning",
                    "Let's role-play: I'm meeting you for the first time",
                    "How do I ask someone how they are?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,      # must practice at least 6 of the vocab items
                    "messages_exchanged": 8,    # must have at least 8 messages in this lesson
                },
            },
            {
                "id": "1.2",
                "title": "Numbers & Counting",
                # ...
            },
            {
                "id": "1.3",
                "title": "Polite Expressions",
                # ...
            },
        ],
    },
    {
        "level": 2,
        "title": "Daily Life",
        "lessons": [
            {"id": "2.1", "title": "Ordering Food & Drinks", ...},
            {"id": "2.2", "title": "Shopping & Prices", ...},
            {"id": "2.3", "title": "Asking for Directions", ...},
            {"id": "2.4", "title": "Transport & Getting Around", ...},
        ],
    },
    {
        "level": 3,
        "title": "Conversations",
        "lessons": [
            {"id": "3.1", "title": "Talking About Family", ...},
            {"id": "3.2", "title": "Weather & Small Talk", ...},
            {"id": "3.3", "title": "At the Hotel", ...},
            {"id": "3.4", "title": "Emergencies & Health", ...},
        ],
    },
]
```

#### Key functions in `curriculum.py`

- `get_all_levels()` → returns the full curriculum structure
- `get_lesson(lesson_id)` → returns a single lesson by ID (e.g., `"1.1"`)
- `get_lesson_vocabulary(lesson_id)` → returns vocab list for a lesson
- `get_lesson_prompts(lesson_id)` → returns practice prompts for a lesson
- `get_next_lesson(current_lesson_id, completed_lessons)` → returns the next uncompleted lesson

#### Integration with existing modules

- **`prompts.py`**: When a lesson is active, `get_recommended_prompts()` pulls from the lesson's `practice_prompts` instead of the generic category-based prompts. The existing deduplication and follow-up logic still applies.
- **`goals.py`**: When a user starts a lesson, auto-create goals from the lesson objectives (e.g., "Practice 6 greetings vocabulary items"). The existing goal completion detection can check against lesson vocabulary.
- **`llm.py`**: Inject the active lesson's vocabulary into the system prompt so the LLM focuses on teaching those specific words/phrases. Add a line like: `"You are currently teaching Lesson 1.1: Greetings & Introductions. Focus on these vocabulary items: ..."`
- **`chat.py`**: Add a lesson selector in the sidebar (below the mode toggle). Show current lesson title, a "Start Lesson" button, and lesson navigation (previous/next). When a lesson is active, the sidebar shows lesson-specific vocabulary as a reference card.

#### UI Changes in `chat.py`

- **Sidebar — Lesson panel** (above the goals section):
  - Dropdown or expander showing levels and lessons
  - Current lesson highlighted with progress indicator
  - "Start Lesson" / "Next Lesson" buttons
  - Lesson vocabulary displayed as a compact reference card (Malay → English)
- **Chat area**: When a lesson is active, the welcome message changes to introduce the lesson topic and objectives
- **Recommended prompts**: Sourced from the active lesson's `practice_prompts` instead of generic categories

---

### Feature B: Progress Tracking (Persistence) — COMPLETE

**New module: `malaychat/progress.py`**

Persistent progress storage using Google Sheets via `gspread`. A single Google Sheet acts as a key-value store, surviving Streamlit Cloud restarts/redeploys. Requires a Google Cloud service account with Sheets + Drive API access, shared with the target spreadsheet.

#### Data Model

```python
# ~/.malaychat/progress.json
{
    "user_id": "default",          # single-user for now
    "created_at": "2026-03-13",
    "current_lesson": "1.1",       # active lesson ID
    "completed_lessons": ["1.1", "1.2"],   # lesson IDs completed
    "vocabulary": {
        # word → metadata (tracks every word the user has practiced)
        "Selamat pagi": {
            "english": "Good morning",
            "lesson_id": "1.1",
            "times_seen": 5,
            "first_seen": "2026-03-13",
            "last_seen": "2026-03-14",
        },
        # ...
    },
    "sessions": [
        {
            "date": "2026-03-13",
            "lesson_id": "1.1",
            "messages_count": 12,
            "vocab_practiced": ["Selamat pagi", "Apa khabar?", ...],
            "duration_minutes": 15,
        },
        # ...
    ],
    "stats": {
        "total_sessions": 8,
        "total_messages": 94,
        "total_vocab_learned": 23,
        "current_streak_days": 3,
        "longest_streak_days": 5,
        "last_session_date": "2026-03-14",
    },
}
```

#### Key functions in `progress.py`

- `load_progress()` → reads JSON file, returns progress dict (creates default if missing)
- `save_progress(progress)` → writes progress dict to JSON file
- `complete_lesson(lesson_id)` → marks a lesson as completed, advances `current_lesson`
- `record_vocab(word, english, lesson_id)` → adds/updates a vocabulary entry (increments `times_seen`)
- `record_session(lesson_id, messages_count, vocab_practiced)` → appends a session record, updates stats and streak
- `get_streak()` → calculates current streak from session dates
- `get_level_progress(level)` → returns fraction of lessons completed in a level
- `reset_progress()` → clears all progress (with confirmation)

#### Vocabulary Detection

Add a function to extract Malay vocabulary from assistant responses. This hooks into the existing response flow in `chat.py`:

```python
def extract_vocabulary(response: str, lesson_vocab: list[dict]) -> list[str]:
    """
    Check which lesson vocabulary items appear in the assistant's response.
    Uses the bold markdown pattern (**word**) that the LLM already produces
    in its breakdown format.
    """
```

This runs after each assistant response (alongside the existing `check_goal_completion`), updating the user's vocabulary record.

#### Lesson Completion Detection

A lesson is complete when the user meets **both** criteria from the lesson's `completion_criteria`:
1. Practiced enough vocabulary items (detected via `extract_vocabulary`)
2. Exchanged enough messages within the lesson

```python
def check_lesson_completion(lesson_id: str, progress: dict) -> bool:
    """Check if a lesson's completion criteria are met."""
    lesson = get_lesson(lesson_id)
    criteria = lesson["completion_criteria"]

    # Count vocab practiced in this lesson's sessions
    lesson_sessions = [s for s in progress["sessions"] if s["lesson_id"] == lesson_id]
    all_vocab = set()
    total_messages = 0
    for session in lesson_sessions:
        all_vocab.update(session["vocab_practiced"])
        total_messages += session["messages_count"]

    return (
        len(all_vocab) >= criteria["vocab_practiced"]
        and total_messages >= criteria["messages_exchanged"]
    )
```

#### UI — Progress Dashboard in Sidebar

Add a progress section to the sidebar in `chat.py`:

- **Streak counter**: "🔥 3-day streak" (or "Start your streak today!")
- **Level progress bars**: For each level, show a progress bar (e.g., "Level 1: 2/3 lessons")
- **Stats summary**: Total vocabulary learned, total sessions, total time
- **Vocabulary journal button**: Opens an expander showing all learned vocabulary, grouped by lesson, with `times_seen` count

#### UI — Lesson Completion Flow

When `check_lesson_completion` returns `True`:
1. Show a `st.balloons()` celebration
2. Toast notification: "Lesson 1.1 complete! You've mastered Greetings & Introductions"
3. Auto-advance `current_lesson` to the next lesson
4. Show a "Continue to next lesson" button

---

### Implementation Order

These features should be built in this order due to dependencies:

1. **`malaychat/curriculum.py`** — Define the curriculum data structure and access functions. No dependencies on other modules.
2. **`malaychat/progress.py`** — Build the persistence layer (JSON read/write, progress data model). Depends on curriculum for lesson IDs.
3. **Integrate curriculum into `chat.py` sidebar** — Add lesson selector, vocabulary reference card, and lesson navigation. Depends on curriculum.py.
4. **Integrate curriculum into `prompts.py`** — Replace generic prompts with lesson-specific prompts when a lesson is active. Depends on curriculum.py.
5. **Integrate curriculum into `llm.py`** — Inject active lesson context into the system prompt. Depends on curriculum.py.
6. **Wire up vocabulary detection in `chat.py`** — After each assistant response, extract vocabulary and record it in progress. Depends on progress.py + curriculum.py.
7. **Wire up lesson completion in `chat.py`** — After vocabulary detection, check if the lesson is complete. Depends on progress.py.
8. **Add progress dashboard to sidebar** — Streak, level progress bars, stats, vocabulary journal. Depends on progress.py.
9. **Session recording** — Record session data (messages, duration, vocab) on session end or lesson switch. Depends on progress.py.

### Files Changed

| File | Change |
|------|--------|
| `malaychat/curriculum.py` | **NEW** — Curriculum data structure and access functions |
| `malaychat/progress.py` | **NEW** — Google Sheets progress persistence, vocabulary tracking, streak calculation |
| `malaychat/chat.py` | Add lesson selector, progress dashboard, vocabulary detection hook, lesson completion flow |
| `malaychat/prompts.py` | Accept active lesson parameter; pull from lesson prompts when available |
| `malaychat/llm.py` | Inject active lesson vocabulary/context into system prompt |
| `malaychat/goals.py` | Auto-create goals from lesson objectives when a lesson starts |
| `ARCHITECTURE.md` | Document new modules and updated data flow |

---

## Phase 3: Launch & Iterate — NOT STARTED

## Phase 4: Growth & Enhancement — NOT STARTED
