# MalayChat Architecture

## Overview

MalayChat is a Malay language learning app using a **two-model architecture with tool calling**:
- **Molmo2-8B** (`allenai/Molmo2-8B`) — LLM via PublicAI Inference API (no local GPU needed)
- **mesolitica/nanot5-base-malaysian-translation-v2.1** — runs locally (~300MB), wrapped as tool objects (`translate_to_malay`, `translate_to_english`)

A pattern-based router decides when to invoke translation tools. Tool results are injected into the LLM's system prompt, so the LLM uses verified translations rather than guessing. Tool calls are visible in the UI via `st.status` widgets.

## Directory Structure

```
tutor/
├── main.py              # Entry point — run with `streamlit run main.py`
├── pyproject.toml       # Project config and dependencies (managed by uv)
├── packages.txt         # System dependencies for Streamlit Cloud
├── .streamlit/
│   └── secrets.toml.example  # Template for PUBLICAI_API_KEY
├── prd.md               # Product requirements document
├── malaychat/
│   ├── __init__.py
│   ├── chat.py          # Streamlit UI: chat interface, sidebar, mode toggle
│   ├── model.py         # Orchestrator: routes tools then streams LLM
│   ├── tools.py         # Tool definitions + pattern-based routing logic
│   ├── llm.py           # Molmo2-8B via PublicAI Inference API with streaming
│   ├── translator.py    # nanot5 translation (runs locally, consumed by tools.py)
│   └── goals.py         # Goal CRUD and completion detection
├── ARCHITECTURE.md      # This file
└── PROGRESS.md          # Implementation progress tracker
```

> **Note:** The package was originally named `app/` but was renamed to `malaychat/` to avoid a namespace collision with Streamlit's internal `app` module, which caused `KeyError: 'app.goals'` on Streamlit Cloud.

## Module Responsibilities

### `malaychat/tools.py` — Tool Definitions & Router
- Defines `Tool` and `ToolOutput` dataclasses (lightweight replacements for LlamaIndex `FunctionTool`)
- `translate_to_malay_tool` and `translate_to_english_tool` wrap the nanot5 translator
- `route_and_call_tools(user_message)` uses regex patterns to detect when translation is needed
- `_extract_phrase()` pulls out the specific phrase to translate (handles quoted text, "how do I say X", etc.)

### `malaychat/model.py` — Orchestrator
- `get_tool_results()` — calls `route_and_call_tools()`, returned separately so chat.py can display tool calls before streaming
- `stream_response()` — formats `ToolOutput` results into context string and passes to LLM

### `malaychat/llm.py` — Molmo2-8B (PublicAI Inference API)
- Uses `requests` to call PublicAI's OpenAI-compatible endpoint (`https://api.publicai.co/v1/chat/completions`)
- Model: `allenai/Molmo2-8B`
- SSE streaming with `max_tokens=1024`
- Parses both `content` and `reasoning_content` delta fields
- Repetition detection (`_is_repeating()`) to stop runaway generation
- Reads `PUBLICAI_API_KEY` from Streamlit secrets

### `malaychat/translator.py` — nanot5 (Local Translation)
- Loads `mesolitica/nanot5-base-malaysian-translation-v2.1` locally (~300MB)
- `to_malay(text)` / `to_english(text)` — consumed by the tools in `tools.py`
- Cached with `@st.cache_resource` so the model loads only once

### `malaychat/goals.py` — Goal Management
- Goals in `st.session_state.goals` as `[{"text": str, "completed": bool}]`
- Keyword-based completion detection on assistant responses (with stop-word filtering)
- Active goals are injected into the LLM system prompt in Learning Mode

### `malaychat/chat.py` — Streamlit Interface
- Mode toggle (Learning/Chat), goal sidebar with add/remove/completion tracking
- **Tool call visibility**: Before streaming the LLM response, tool calls are displayed using `st.status` widgets showing the tool name, input phrase, and translation result
- `st.write_stream()` for token-by-token display
- Toast notifications on goal completion
- Goals counter metric in sidebar

## Data Flow

```
User Input ("How do I say thank you?")
    │
    ▼
┌──────────────┐
│  chat.py     │  ← receives user input
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  model.py    │  ← get_tool_results()
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
       │
       ▼
┌──────────────┐     st.status widget shows tool call + result
│  chat.py     │────▶ "Translating to Malay..."
└──────┬───────┘       translate_to_malay("thank you") → "terima kasih"
       │
       ▼
┌──────────────┐     tool_context: 'translate_to_malay: "thank you" → "terima kasih"'
│  model.py    │  ← stream_response()
└──────┬───────┘
       │
       ▼
┌──────────────┐     system prompt + tool results + chat history
│   llm.py     │
│ (Molmo2-8B / │────▶ streamed tokens ────▶ st.write_stream()
│  PublicAI)   │     (SSE streaming, content + reasoning_content)
└──────────────┘
       │
       ▼
┌──────────────┐
│  goals.py    │  ← checks for goal completion (Learning Mode only)
└──────────────┘
```

## Key Design Decisions

1. **PublicAI Inference API for LLM**: No local GPU/memory needed, deploys on Streamlit Cloud within 1GB RAM. Uses Molmo2-8B via PublicAI's OpenAI-compatible endpoint.
2. **Local translator**: nanot5 is small (~300MB) and runs locally for fast, reliable translations without additional API latency.
3. **Pattern-based tool routing**: Regex patterns detect when translation is needed. Small models can't reliably do structured ReAct-style tool calling, so pattern matching is more robust.
4. **Selective tool use**: Only translation-related queries trigger tool calls. General conversation goes directly to the LLM.
5. **Visible tool calls**: Tool calls are shown in the UI via `st.status` widgets before the LLM response streams, so users can see what translation happened.
6. **SSE streaming**: Both `content` and `reasoning_content` delta fields are parsed from the SSE stream, ensuring responses are never empty.
7. **Package naming**: `malaychat/` instead of `app/` to avoid Streamlit's internal namespace collision.
8. **Streaming with safety**: Token streaming with repetition detection to catch and stop runaway generation loops.
