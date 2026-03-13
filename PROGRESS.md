# MalayChat Progress

## Phase 1: MVP Foundation — COMPLETE

### Week 1-2: Model Integration
- [x] Set up project with `uv` package manager (Python 3.13)
- [x] Dependencies: streamlit, transformers, torch, sentencepiece, huggingface-hub
- [x] **Two-model architecture with tool calling**:
  - `malaychat/llm.py` — Apriel 1.6 15B Thinker (`ServiceNow-AI/Apriel-1.6-15b-Thinker:together`) via HuggingFace free Inference API
  - `malaychat/translator.py` — nanot5 translation model runs locally (~300MB)
  - `malaychat/tools.py` — Tool definitions (`Tool`/`ToolOutput` dataclasses) + pattern-based routing
  - `malaychat/model.py` — Orchestrator: routes tools → injects results → streams LLM
- [x] HF Inference API streaming via `InferenceClient.chat_completion(stream=True)`
- [x] Reasoning model support: both `reasoning_content` and `content` tokens yielded to user, empty `choices[]` chunks handled, `max_tokens=1024` for reasoning overhead
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
- [x] `.streamlit/secrets.toml.example` for HF_TOKEN configuration
- [x] Iterated through multiple LLM approaches before settling on DeepSeek R1 via HF Inference API:
  - mallam-3B → SeaLLMs → Llama 3.2 (various quantizations) → HF Inference API → DeepSeek R1 → Apriel 1.6 15B Thinker
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
2. Add `HF_TOKEN` in Streamlit Cloud Settings > Secrets (get a free token at https://huggingface.co/settings/tokens)

---

## Phase 2: Core Experience — NOT STARTED
- [ ] Auto-goal suggestions based on conversation context
- [ ] Session history (save/review past conversations)
- [ ] Progress dashboard
- [ ] Vocabulary highlighting
- [ ] Example phrases library

## Phase 3: Launch & Iterate — NOT STARTED

## Phase 4: Growth & Enhancement — NOT STARTED
