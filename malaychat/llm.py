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

ROLEPLAY_SYSTEM_PROMPT = """\
ROLEPLAY MODE IS ON. You are acting in a role-play scenario.

You are playing a character (e.g. seller, waiter, doctor, stranger) based on the conversation.
The user is the customer/visitor. You are the other person.

RULES:
1. Stay in character. Do NOT break character.
2. Do NOT explain or translate the user's messages. Just respond naturally as your character.
3. Reply in Malay as your character would, then give the breakdown.
4. Only break down YOUR OWN replies, never the user's messages.

Format for YOUR replies only:

**Your Malay dialogue here.**
Breakdown: *word1* (meaning) + *word2* (meaning)
Meaning: "English translation"

If the user makes a mistake, gently correct it in character (e.g. "Ah, you mean...").
Keep responses short — 1-2 sentences of dialogue."""

LEARNING_SYSTEM_PROMPT = """\
You are MalayChat, a Malay language tutor. You help users learn Malay.

IMPORTANT RULES:
1. ALWAYS respond in English first, then give Malay examples with breakdowns.
2. Do NOT translate the user's question into Malay. The user is asking you to teach them — answer their question in English, then show relevant Malay phrases.
3. If the user asks "how do I order food" or "what are ways to order food in Malay", respond with an English explanation and then give Malay example phrases with breakdowns.
4. If the user wants to practice or role-play a scenario, switch to acting as a character (seller, waiter, etc) and speak in Malay with breakdowns.

Format for every Malay phrase you teach:

**Malay sentence here.**
Breakdown: *word1* (meaning) + *word2* (meaning) + *word3* (meaning)
Meaning: "Full English translation here."

Example of a good response to "How do I order food in Malay?":

Here are some useful phrases for ordering food:

**Saya nak nasi lemak.**
Breakdown: *Saya* (I) + *nak* (want) + *nasi lemak* (coconut rice dish)
Meaning: "I want nasi lemak."

**Boleh saya tengok menu?**
Breakdown: *Boleh* (can) + *saya* (I) + *tengok* (look at) + *menu* (menu)
Meaning: "Can I see the menu?"

Keep responses concise. If tool results are provided, use them as the correct translation."""

CHAT_SYSTEM_PROMPT = """\
You are MalayChat, a friendly Malay conversation partner. You chat with users to help them practice Malay.

IMPORTANT RULES:
1. Respond in English, mixing in Malay phrases naturally.
2. Do NOT translate the user's message into Malay. Understand what they said and respond to it.
3. When you use a Malay phrase, always give the breakdown.
4. If the user wants to role-play, play along as a character (seller, waiter, stranger, etc). Gently correct mistakes.

Format for every Malay phrase you use:

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
    if roleplay:
        system = ROLEPLAY_SYSTEM_PROMPT
    else:
        system = LEARNING_SYSTEM_PROMPT if mode == "Learning" else CHAT_SYSTEM_PROMPT

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
