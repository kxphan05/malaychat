# MalayChat Architecture

## Overview

MalayChat is a locally-run Malay language learning app using a **two-model architecture with LlamaIndex tool calling**:
- **Llama 3.2 1B Instruct (Q4_K_M GGUF)** — handles tutoring logic, conversation, and instruction following
- **mesolitica/nanot5-base-malaysian-translation-v2.1** — wrapped as LlamaIndex `FunctionTool` objects (`translate_to_malay`, `translate_to_english`)

A pattern-based router in `tools.py` decides when to invoke translation tools. Tool results are injected into the LLM's system prompt as context, so the LLM uses verified translations rather than guessing.

## Directory Structure

```
tutor/
├── main.py              # Entry point — run with `streamlit run main.py`
├── pyproject.toml       # Project config and dependencies (managed by uv)
├── prd.md               # Product requirements document
├── app/
│   ├── __init__.py
│   ├── chat.py          # Streamlit UI: chat interface, sidebar, mode toggle
│   ├── model.py         # Orchestrator: routes tools then streams LLM
│   ├── tools.py         # LlamaIndex FunctionTool definitions + routing logic
│   ├── llm.py           # Llama 3.2 GGUF loading and streaming via llama-cpp
│   ├── translator.py    # nanot5 translation (consumed by tools.py)
│   └── goals.py         # Goal CRUD and completion detection
├── ARCHITECTURE.md      # This file
└── PROGRESS.md          # Implementation progress tracker
```

## Module Responsibilities

### `app/tools.py` — LlamaIndex Tool Definitions & Router
- Defines `translate_to_malay_tool` and `translate_to_english_tool` as `FunctionTool.from_defaults()` wrapping the nanot5 translator
- `route_and_call_tools(user_message)` uses regex patterns to detect when translation is needed:
  - "how do I say X", "translate X to malay", "what is X in malay" → `translate_to_malay`
  - "what does X mean", "translate X to english" → `translate_to_english`
  - General conversation → no tool call
- `_extract_phrase()` pulls out the specific phrase to translate from the user's message
- Returns `ToolOutput` objects with the translation results

### `app/model.py` — Orchestrator
- Calls `route_and_call_tools()` to check if tools are needed
- Formats `ToolOutput` results into a context string
- Passes tool context + messages to the LLM for response generation

### `app/llm.py` — Llama 3.2 (Chat LLM)
- Downloads `hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF` via `hf_hub_download`
- Loads GGUF with `llama-cpp-python` (cached with `@st.cache_resource`)
- Streaming via `create_chat_completion(stream=True)`
- Tool results injected into system prompt so the LLM uses verified translations
- Repetition detection to stop runaway generation

### `app/translator.py` — nanot5 (Translation Engine)
- Loads `mesolitica/nanot5-base-malaysian-translation-v2.1` via HuggingFace Transformers
- `to_malay(text)` / `to_english(text)` — consumed by the FunctionTools in `tools.py`

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
│   FuncTools) │            │
└──────┬───────┘            ▼
       │             ┌──────────────┐
       │             │ translator.py│  → "terima kasih"
       │             │ (nanot5)     │
       │             └──────────────┘
       │  tool_context: 'translate_to_malay: "thank you" → "terima kasih"'
       ▼
┌──────────────┐     system prompt + tool results + chat history
│   llm.py     │
│  (Llama 3.2  │────▶ streamed tokens ────▶ st.write_stream()
│   GGUF)      │
└──────────────┘
       │
       ▼
┌──────────────┐
│  goals.py    │  ← checks for goal completion
└──────────────┘

For "Tell me about yourself" → tools.py returns no tool calls → LLM responds directly
```

## Key Design Decisions

1. **LlamaIndex FunctionTools**: Translation functions are wrapped as `FunctionTool` objects, giving a standardized tool interface with `ToolOutput` results.
2. **Pattern-based routing**: A 1B model can't reliably do ReAct-style tool calling. Instead, regex patterns detect when translation is needed. The LLM only handles conversation — it never sees tool-calling syntax.
3. **Selective tool use**: Only translation-related queries trigger tool calls. General conversation flows directly to the LLM with no translation overhead.
4. **Tool results as context**: Tool outputs are injected into the system prompt as "Tool results (use these translations exactly)", keeping the LLM's job simple — just compose a response using the provided translations.
5. **GGUF + llama-cpp-python**: Q4_K_M quantization for fast CPU inference.
6. **Streaming**: `create_chat_completion(stream=True)` for responsive token-by-token UI.
