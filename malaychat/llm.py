"""PublicAI Inference API for Malay language tutoring."""

import json
import logging
import time
from collections.abc import Generator

import requests
import streamlit as st

from malaychat.curriculum import get_lesson

logger = logging.getLogger("malaychat.llm")

PUBLICAI_URL = "https://api.publicai.co/v1/chat/completions"
MODEL_ID = "allenai/Molmo2-8B"

ROLEPLAY_CONTEXT = """\

ROLEPLAY MODE IS ON. You are currently acting in a role-play scenario with the user.
You MUST stay in character. You are playing a role (e.g. seller, waiter, doctor, stranger) based on the conversation.
The user is the customer/visitor. You are the other person in the scenario.
Do NOT break character. Do NOT translate the user's messages. Respond as your character would.
Use Malay in your dialogue, then provide the breakdown and meaning after each Malay sentence."""

LEARNING_SYSTEM_PROMPT = """\
You are MalayChat, a Malay language tutor. You help users learn Malay through conversation and translation.

IMPORTANT: Do NOT translate the user's question. Instead, understand what they want and respond helpfully.

If the user wants to practice or have a conversation, role-play the scenario. For example, if they say "let's practice at a market", you become a market seller and start the conversation in Malay.

If the user asks how to say something, give the Malay translation with an example.

ALWAYS follow this format for every Malay sentence you write:

**Malay sentence here.**
Breakdown: *word1* (meaning) + *word2* (meaning) + *word3* (meaning)
Meaning: "Full English translation here."

Example of correct output:
**Selamat datang! Nak beli apa?**
Breakdown: *Selamat* (safe/greetings) + *datang* (come/welcome) + *Nak* (want) + *beli* (buy) + *apa* (what)
Meaning: "Welcome! What do you want to buy?"

Keep responses concise. If tool results are provided, use them as the correct translation."""

CHAT_SYSTEM_PROMPT = """\
You are MalayChat, a friendly Malay conversation partner. You chat with users to help them practice Malay.

IMPORTANT: Do NOT translate the user's question. Instead, understand what they want and respond naturally.

If the user wants to practice or role-play, play along as a character (seller, waiter, stranger, etc). Mix Malay and English. Gently correct mistakes.

ALWAYS follow this format for every Malay sentence you write:

**Malay sentence here.**
Breakdown: *word1* (meaning) + *word2* (meaning) + *word3* (meaning)
Meaning: "Full English translation here."

Keep responses concise. If tool results are provided, use them as the correct translation."""


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
    roleplay: bool = False,
    active_lesson_id: str | None = None,
) -> list[dict]:
    """Build chat messages with system prompt and tool results."""
    system = LEARNING_SYSTEM_PROMPT if mode == "Learning" else CHAT_SYSTEM_PROMPT

    if roleplay:
        system += ROLEPLAY_CONTEXT

    # Inject active lesson context
    if active_lesson_id:
        lesson = get_lesson(active_lesson_id)
        if lesson:
            vocab_lines = ", ".join(
                f"{v['malay']} ({v['english']})" for v in lesson["vocabulary"]
            )
            system += (
                f"\n\nYou are currently teaching Lesson {lesson['id']}: {lesson['title']}."
                f"\n{lesson['description']}."
                f"\nFocus on these vocabulary items: {vocab_lines}."
                "\nTry to naturally introduce and practice these words during the conversation."
            )

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
    roleplay: bool = False,
    active_lesson_id: str | None = None,
    max_new_tokens: int = 1024,
) -> Generator[str, None, None]:
    """Stream tokens from the PublicAI Inference API."""
    logger.info("stream_response — mode=%s, roleplay=%s, lesson=%s, messages=%d", mode, roleplay, active_lesson_id, len(messages))

    api_key = get_api_key()
    chat_messages = build_messages(messages, mode, goals, tool_context, roleplay, active_lesson_id)

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
