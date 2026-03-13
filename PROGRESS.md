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
2. Add secrets in Streamlit Cloud Settings > Secrets (see `.streamlit/secrets.toml.example`)

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
  - Toggle switch in the chat area (`st.toggle`), right-aligned above recommended prompts
  - When active, **replaces** the entire system prompt with a dedicated `ROLEPLAY_SYSTEM_PROMPT` (not appended — see PAST_MISTAKES.md #6)
  - Caption updates to show "(Role-play active)"
  - Flows through `chat.py` → `model.py` → `llm.py` → system prompt

---

## Phase 2: Core Experience — COMPLETE

- [x] ~~Auto-goal suggestions based on conversation context~~ (done in Phase 1.5 as recommended prompts)

### Feature A: Structured Learning Template — COMPLETE

**New module: `malaychat/curriculum.py`**

- [x] 3 levels, 11 lessons with full vocabulary (8-12 items each, ~120 total)
  - Level 1 — Foundations: Greetings & Introductions, Numbers & Counting, Polite Expressions
  - Level 2 — Daily Life: Ordering Food, Shopping & Prices, Directions, Transport
  - Level 3 — Conversations: Family, Weather & Small Talk, Hotel, Emergencies
- [x] Each lesson: `id`, `title`, `description`, `vocabulary`, `practice_prompts`, `completion_criteria`
- [x] Access functions: `get_lesson()`, `get_next_lesson()`, `get_lesson_vocabulary()`, `format_vocab_reference()`
- [x] Flat lookup index for O(1) access, ordered `ALL_LESSON_IDS` for navigation
- [x] **Sidebar lesson panel** (Learning mode): expandable levels, Go/Previous/Next/Exit buttons, vocabulary reference card
- [x] **Lesson-aware welcome message**: introduces lesson topic when a lesson is active
- [x] **Lesson-aware prompts**: `prompts.py` pulls from `practice_prompts` when a lesson is active
- [x] **Lesson context in LLM**: active lesson vocabulary injected into system prompt
- [x] **Lesson progress indicators**: vocab and message progress bars in sidebar (e.g., "Vocab: 3/6")
- [x] **Manual "Complete Lesson" button**: lets users mark a lesson done at any time
- [x] **Auto-completion**: triggers when both vocab and message criteria are met (balloons + toast + auto-advance)

### Feature B: Progress Tracking — COMPLETE

**New module: `malaychat/progress.py`**

- [x] Google Sheets persistence via `gspread` (survives Streamlit Cloud restarts)
  - Originally planned as local JSON files, but Streamlit Cloud's ephemeral filesystem made those disappear on restart
  - Considered browser localStorage (simple but single-device) and Supabase (overkill) before settling on Google Sheets
- [x] Key-value sheet layout: `current_lesson`, `completed_lessons`, `vocabulary`, `sessions`, `stats` (JSON-encoded)
- [x] Auto-initializes sheet with defaults on first load
- [x] Vocabulary detection: `extract_vocabulary()` finds lesson vocab in assistant responses (bold markdown + plain text)
- [x] Lesson completion: `check_lesson_completion()` via `get_lesson_progress()` — reuses computed stats (see PAST_MISTAKES.md #8)
- [x] Session recording with streak tracking (consecutive days)
- [x] **Progress dashboard** in sidebar: streak counter, level progress bars, vocab/session metrics, vocabulary journal expander
- [x] **Multi-user support**: each user gets their own worksheet tab (`progress_{username}`)

### Feature C: Authentication — COMPLETE

**New module: `malaychat/auth.py`**

- [x] Simple username/password system using a `users` worksheet tab in the same Google Sheet
- [x] Passwords stored as SHA-256 hashes
- [x] Login/register form with tabs
- [x] Login gate: `render_login()` called at top of `run()`, blocks the app until authenticated
- [x] Username displayed in sidebar with logout button
- [x] Logout clears all session state

### Additional Fixes
- [x] **Recommended prompts not refreshing**: added `st.rerun()` after every message exchange so prompts re-evaluate with updated conversation history (see PAST_MISTAKES.md #7)
- [x] **Role-play toggle position**: moved from top of chat area (scrolled away) to right-aligned above recommended prompts, near the input area
- [x] **Role-play prompt conflict**: changed from appending `ROLEPLAY_CONTEXT` to replacing the entire system prompt with `ROLEPLAY_SYSTEM_PROMPT` (see PAST_MISTAKES.md #6)

### Dependencies Added
- `gspread>=6.0.0` — Google Sheets API client
- `google-auth>=2.20.0` — Google service account authentication

### Secrets Required
```toml
PUBLICAI_API_KEY = "..."
PROGRESS_SHEET_URL = "https://docs.google.com/spreadsheets/d/.../edit"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

---

## Phase 3: Launch & Iterate — NOT STARTED

## Phase 4: Growth & Enhancement — NOT STARTED
