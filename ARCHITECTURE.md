# MalayChat Architecture

## Overview

MalayChat is a Malay language learning app using a **two-model architecture with tool calling**:
- **Llama 3.2 3B Instruct** — via HuggingFace Inference API (free tier, no local GPU needed)
- **mesolitica/nanot5-base-malaysian-translation-v2.1** — runs locally, wrapped as tool objects (`translate_to_malay`, `translate_to_english`)

A pattern-based router decides when to invoke translation tools. Tool results are injected into the LLM's system prompt, so the LLM uses verified translations rather than guessing.

## Directory Structure

```
tutor/
├── main.py              # Entry point — run with `streamlit run main.py`
├── pyproject.toml       # Project config and dependencies (managed by uv)
├── packages.txt         # System dependencies for Streamlit Cloud
├── .streamlit/
│   └── secrets.toml.example  # Template for HF_TOKEN
├── prd.md               # Product requirements document
├── app/
│   ├── __init__.py
│   ├── chat.py          # Streamlit UI: chat interface, sidebar, mode toggle
│   ├── model.py         # Orchestrator: routes tools then streams LLM
│   ├── tools.py         # Tool definitions + pattern-based routing logic
│   ├── llm.py           # HuggingFace Inference API client with streaming
│   ├── translator.py    # nanot5 translation (runs locally, consumed by tools.py)
│   └── goals.py         # Goal CRUD and completion detection
├── ARCHITECTURE.md      # This file
└── PROGRESS.md          # Implementation progress tracker
```

## Module Responsibilities

### `app/tools.py` — Tool Definitions & Router
- Defines `Tool` and `ToolOutput` dataclasses
- `translate_to_malay_tool` and `translate_to_english_tool` wrap the nanot5 translator
- `route_and_call_tools(user_message)` uses regex patterns to detect when translation is needed
- `_extract_phrase()` pulls out the specific phrase to translate

### `app/model.py` — Orchestrator
- Calls `route_and_call_tools()` to check if tools are needed
- Formats `ToolOutput` results into a context string
- Passes tool context + messages to the LLM for response generation

### `app/llm.py` — Llama 3.2 (HuggingFace Inference API)
- Uses `InferenceClient` from `huggingface_hub` — no local model loading
- Calls `meta-llama/Llama-3.2-3B-Instruct` via HF's free Inference API
- Streaming via `chat_completion(stream=True)`
- Reads `HF_TOKEN` from Streamlit secrets (optional for public models)
- Repetition detection to stop runaway generation

### `app/translator.py` — nanot5 (Local Translation)
- Loads `mesolitica/nanot5-base-malaysian-translation-v2.1` locally (~300MB)
- `to_malay(text)` / `to_english(text)` — consumed by the tools in `tools.py`

### `app/goals.py` — Goal Management
- Goals in `st.session_state.goals` as `[{"text": str, "completed": bool}]`
- Keyword-based completion detection on assistant responses

### `app/chat.py` — Streamlit Interface
- Mode toggle (Learning/Chat), goal sidebar, `st.write_stream()` for token display

## Data Flow

```
User Input ("How do I say thank you?")
    │
    ▼
┌──────────────┐
│  model.py    │  ← orchestrator
└──────┬───────┘
       │
       ▼
┌──────────────┐     pattern match → "thank you" needs translation
│  tools.py    │
│  (router +   │────▶ translate_to_malay_tool.call("thank you")
│   tools)     │            │
└──────┬───────┘            ▼
       │             ┌──────────────┐
       │             │ translator.py│  → "terima kasih" (local)
       │             │ (nanot5)     │
       │             └──────────────┘
       │  tool_context: 'translate_to_malay: "thank you" → "terima kasih"'
       ▼
┌──────────────┐     system prompt + tool results + chat history
│   llm.py     │
│  (HF Infr.   │────▶ streamed tokens ────▶ st.write_stream()
│   API)       │
└──────────────┘
       │
       ▼
┌──────────────┐
│  goals.py    │  ← checks for goal completion
└──────────────┘
```

## Key Design Decisions

1. **HuggingFace Inference API for LLM**: Free, no local GPU/memory needed, deploys anywhere. Uses the 3B model (better quality than 1B) since inference runs on HF servers.
2. **Local translator**: nanot5 is small (~300MB) and runs locally for fast, reliable translations without API latency.
3. **Pattern-based tool routing**: Regex patterns detect when translation is needed. The LLM only handles conversation.
4. **Selective tool use**: Only translation-related queries trigger tool calls. General conversation goes directly to the API.
5. **Streaming**: HF Inference API supports streaming via `chat_completion(stream=True)`.
6. **Deployable on Streamlit Cloud**: No C compiler, no large model downloads, fits in 1GB RAM.
