"""PublicAI Inference API for Malay language tutoring."""

import json
import logging
import time
from collections.abc import Generator

import requests
import streamlit as st

logger = logging.getLogger("malaychat.llm")

PUBLICAI_URL = "https://api.publicai.co/v1/chat/completions"
MODEL_ID = "allenai/Molmo2-8B"

LEARNING_SYSTEM_PROMPT = """\
You are MalayChat, a Malay language tutor.

Rules:
- Keep responses concise.
- Answer ONLY what the user asked.
- Use the provided tool results for Malay translations. Do NOT guess or invent Malay words.
- Format each phrase as: **Malay phrase** — English meaning
- Add one short example sentence, then break it down word by word so the user understands each part. Use this format:
  Example: **Sila ambil talian untuk membuat simpanan.**
  Breakdown: *Sila* (please) + *ambil* (take) + *talian* (number/line) + *untuk* (to/for) + *membuat* (make) + *simpanan* (deposit/savings)
  Meaning: "Please take a number to make a deposit."
- Do NOT ramble, do NOT add unrelated facts."""

CHAT_SYSTEM_PROMPT = """\
You are MalayChat, a friendly Malay conversation partner.

Rules:
- Keep responses concise.
- Stay on topic. Only respond to what the user said.
- Use the provided tool results for Malay translations. Do NOT guess Malay words.
- Mix Malay and English naturally.
- Gently correct mistakes if any.
- When you use a Malay sentence, break it down word by word so the user understands each part. Use this format:
  Breakdown: *word1* (meaning) + *word2* (meaning) + ...
  Meaning: {Full English translation}"""


def get_api_key() -> str:
    """Retrieve PublicAI API key from Streamlit secrets."""
    key = st.secrets.get("PUBLICAI_API_KEY", None)
    if not key:
        raise ValueError("PUBLICAI_API_KEY not set in Streamlit secrets")
    return key


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
    max_new_tokens: int = 1024,
) -> Generator[str, None, None]:
    """Stream tokens from the PublicAI Inference API."""
    logger.info("stream_response — mode=%s, messages=%d", mode, len(messages))

    api_key = get_api_key()
    chat_messages = build_messages(messages, mode, goals, tool_context)

    t0 = time.perf_counter()
    token_count = 0
    accumulated = ""

    response = requests.post(
        PUBLICAI_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "messages": chat_messages,
            "max_tokens": max_new_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": True,
        },
        stream=True,
        timeout=60,
    )
    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        data = decoded[6:]
        if data.strip() == "[DONE]":
            break

        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue

        choices = chunk.get("choices", [])
        if not choices:
            continue
        delta = choices[0].get("delta", {})
        text = delta.get("content", "") or delta.get("reasoning_content", "")

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


def _is_repeating(text: str, window: int = 80, min_length: int = 250) -> bool:
    """Detect if output is stuck in a repetition loop."""
    if len(text) < min_length:
        return False
    tail = text[-window:]
    if tail in text[:-window]:
        return True
    for phrase_len in range(30, window // 2):
        phrase = text[-phrase_len:]
        if text.count(phrase) >= 3:
            return True
    return False
