"""Llama 3.2 1B GGUF chat model via llama-cpp-python."""

import logging
import time
from collections.abc import Generator

import streamlit as st
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

logger = logging.getLogger("malaychat.llm")

REPO_ID = "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"
FILENAME = "llama-3.2-1b-instruct-q4_k_m.gguf"

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
def load_llm() -> Llama:
    """Download the GGUF file from HuggingFace and load with llama-cpp-python."""
    logger.info("Downloading GGUF: %s / %s", REPO_ID, FILENAME)
    t0 = time.perf_counter()
    model_path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
    logger.info("Downloaded in %.2fs: %s", time.perf_counter() - t0, model_path)

    logger.info("Loading GGUF model...")
    t0 = time.perf_counter()
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_threads=4,
        verbose=False,
    )
    logger.info("Model loaded in %.2fs", time.perf_counter() - t0)
    return llm


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
    """Stream tokens from Llama 3.2 GGUF."""
    logger.info("stream_response — mode=%s, messages=%d", mode, len(messages))

    llm = load_llm()
    chat_messages = build_messages(messages, mode, goals, tool_context)

    t0 = time.perf_counter()
    token_count = 0
    accumulated = ""

    stream = llm.create_chat_completion(
        messages=chat_messages,
        max_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.3,
        stream=True,
    )

    for chunk in stream:
        delta = chunk["choices"][0]["delta"]
        text = delta.get("content", "")
        if text:
            accumulated += text
            if _is_repeating(accumulated):
                logger.warning("Repetition detected after %d tokens, stopping", token_count)
                break
            token_count += 1
            yield text

    gen_time = time.perf_counter() - t0
    logger.info("Done in %.2fs — %d tokens (%.1f tok/s)", gen_time, token_count,
                token_count / gen_time if gen_time > 0 else 0)


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
