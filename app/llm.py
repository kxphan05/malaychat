"""Llama 3.2 1B GGUF chat model via transformers."""

import logging
import time
from collections.abc import Generator
from threading import Thread

import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

logger = logging.getLogger("malaychat.llm")

REPO_ID = "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"
GGUF_FILE = "llama-3.2-1b-instruct-q4_k_m.gguf"

LEARNING_SYSTEM_PROMPT = """\
You are MalayChat, a Malay language tutor.

Rules:
- Keep responses to 2-4 sentences max.
- Answer ONLY what the user asked.
- Use the provided tool results for Malay translations. Do NOT guess or invent Malay words.
- Format each phrase as: **Malay phrase** — English meaning
- Add one short example showing how to use the phrase.
- Do NOT ramble, do NOT add unrelated facts."""

CHAT_SYSTEM_PROMPT = """\
You are MalayChat, a friendly Malay conversation partner.

Rules:
- Keep responses to 2-4 sentences max.
- Stay on topic. Only respond to what the user said.
- Use the provided tool results for Malay translations. Do NOT guess Malay words.
- Mix Malay and English naturally.
- Gently correct mistakes if any."""


@st.cache_resource(show_spinner="Downloading and loading Llama 3.2 1B GGUF...")
def load_llm() -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load the GGUF model via transformers (no C compiler needed)."""
    logger.info("Loading GGUF model: %s / %s", REPO_ID, GGUF_FILE)
    t0 = time.perf_counter()

    tokenizer = AutoTokenizer.from_pretrained(REPO_ID, gguf_file=GGUF_FILE)
    model = AutoModelForCausalLM.from_pretrained(
        REPO_ID,
        gguf_file=GGUF_FILE,
        torch_dtype=torch.float32,
        device_map="cpu",
    )

    logger.info("Model loaded in %.2fs", time.perf_counter() - t0)
    return model, tokenizer


def build_messages(
    messages: list[dict],
    mode: str,
    goals: list[dict],
    tool_context: str,
) -> list[dict]:
    """Build chat messages with system prompt and tool results."""
    system = LEARNING_SYSTEM_PROMPT if mode == "Learning" else CHAT_SYSTEM_PROMPT

    if mode == "Learning" and goals:
        active = [g["text"] for g in goals if not g["completed"]]
        if active:
            system += (
                "\n\nThe user's current learning goals:\n"
                + "\n".join(f"- {g}" for g in active)
            )

    if tool_context:
        system += f"\n\nTool results (use these translations exactly):\n{tool_context}"

    return [{"role": "system", "content": system}, *messages]


def stream_response(
    messages: list[dict],
    mode: str,
    goals: list[dict],
    tool_context: str,
    max_new_tokens: int = 200,
) -> Generator[str, None, None]:
    """Stream tokens from Llama 3.2 GGUF via transformers."""
    logger.info("stream_response — mode=%s, messages=%d", mode, len(messages))

    model, tokenizer = load_llm()
    chat_messages = build_messages(messages, mode, goals, tool_context)

    prompt = tokenizer.apply_chat_template(
        chat_messages, tokenize=False, add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = inputs["input_ids"].shape[1]
    logger.info("Tokenized: %d tokens", input_len)

    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True,
    )

    generate_kwargs = dict(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.3,
        no_repeat_ngram_size=4,
        streamer=streamer,
    )

    t0 = time.perf_counter()
    thread = Thread(target=_generate_in_thread, args=(model, generate_kwargs))
    thread.start()

    token_count = 0
    accumulated = ""
    stopped_early = False
    for chunk in streamer:
        if chunk:
            accumulated += chunk
            if _is_repeating(accumulated):
                logger.warning("Repetition detected, stopping early")
                stopped_early = True
                break
            token_count += 1
            yield chunk

    if stopped_early:
        for _ in streamer:
            pass

    thread.join()
    gen_time = time.perf_counter() - t0
    logger.info("Done in %.2fs — %d tokens%s", gen_time, token_count,
                " (stopped: repetition)" if stopped_early else "")


def _generate_in_thread(model: AutoModelForCausalLM, kwargs: dict) -> None:
    """Run model.generate in a background thread."""
    try:
        with torch.no_grad():
            model.generate(**kwargs)
    except Exception:
        logger.exception("model.generate() failed")


def _is_repeating(text: str, window: int = 60, min_length: int = 80) -> bool:
    """Detect if output is stuck in a repetition loop."""
    if len(text) < min_length:
        return False
    tail = text[-window:]
    if tail in text[:-window]:
        return True
    for phrase_len in range(15, window // 2):
        phrase = text[-phrase_len:]
        if text.count(phrase) >= 3:
            return True
    return False
