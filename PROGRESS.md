# MalayChat Progress

## Phase 1: MVP Foundation — COMPLETE

### Week 1-2: Model Integration
- [x] Set up project with `uv` package manager (Python 3.13)
- [x] Dependencies: streamlit, transformers, torch, sentencepiece, huggingface-hub
- [x] **Two-model architecture with tool calling**:
  - `app/llm.py` — Llama 3.2 3B Instruct via HuggingFace free Inference API
  - `app/translator.py` — nanot5 translation model runs locally (~300MB)
  - `app/tools.py` — Tool definitions + pattern-based routing
  - `app/model.py` — orchestrator: routes tools → injects results → streams LLM
- [x] HF Inference API streaming via `InferenceClient.chat_completion(stream=True)`
- [x] Repetition detection (streaming-side loop detector)
- [x] Comprehensive logging throughout the pipeline
- [x] Deployable on Streamlit Cloud (no C compiler, fits in 1GB RAM)

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
Working prototype ready for deployment.

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
