# MalayChat Progress

## Phase 1: MVP Foundation — COMPLETE

### Week 1-2: Model Integration
- [x] Set up project with `uv` package manager (Python 3.13)
- [x] Dependencies: streamlit, llama-index-core, llama-index-llms-llama-cpp, transformers, torch, sentencepiece
- [x] **Two-model architecture with LlamaIndex tool calling**:
  - `app/llm.py` — Llama 3.2 1B (Q4_K_M GGUF) for tutoring via llama-cpp-python
  - `app/translator.py` — nanot5 translation model via HuggingFace Transformers
  - `app/tools.py` — LlamaIndex `FunctionTool` definitions + pattern-based routing
  - `app/model.py` — orchestrator: routes tools → injects results → streams LLM
- [x] GGUF model auto-downloaded from HuggingFace and cached locally
- [x] LLM cached via `@st.cache_resource`
- [x] Token streaming via `create_chat_completion(stream=True)`
- [x] Repetition detection (repeat_penalty + streaming loop detector)
- [x] Comprehensive logging throughout the pipeline

### Week 3: Streamlit Chat Interface
- [x] Built `app/chat.py` with full chat UI
- [x] Mode toggle: Learning Mode (structured practice) and Chat Mode (freeform)
- [x] Chat message history with Streamlit's `st.chat_message`
- [x] Token-by-token streaming display via `st.write_stream()`
- [x] Welcome message with usage instructions
- [x] Clear chat button

### Week 4: Goal Sidebar
- [x] Goal sidebar in `app/goals.py` with add/remove functionality
- [x] Visual completion indicators (checkmark vs empty box)
- [x] Automatic goal completion detection via keyword matching in responses
- [x] Toast notifications on goal completion
- [x] Goals counter metric in sidebar
- [x] Empty state with suggested starter goals
- [x] Goals injected into system prompt so model works toward them

### Deliverable
Working prototype ready for internal testing. Run with:
```bash
uv run streamlit run main.py
```

---

## Phase 2: Core Experience — NOT STARTED
- [ ] Auto-goal suggestions based on conversation context
- [ ] Session history (save/review past conversations)
- [ ] Progress dashboard
- [ ] Vocabulary highlighting
- [ ] Example phrases library

## Phase 3: Launch & Iterate — NOT STARTED

## Phase 4: Growth & Enhancement — NOT STARTED
