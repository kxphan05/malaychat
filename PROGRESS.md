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

---

## Phase 2: Core Experience — NOT STARTED
- [ ] Auto-goal suggestions based on conversation context
- [ ] Session history (save/review past conversations)
- [ ] Progress dashboard
- [ ] Vocabulary highlighting
- [ ] Example phrases library

## Phase 3: Launch & Iterate — NOT STARTED

## Phase 4: Growth & Enhancement — NOT STARTED
