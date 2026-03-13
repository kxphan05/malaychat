"""Orchestrator: routes to LlamaIndex tools, then streams LLM response."""

import logging
from collections.abc import Generator

from app.llm import stream_response as llm_stream
from app.tools import route_and_call_tools

logger = logging.getLogger("malaychat.model")


def stream_response(
    messages: list[dict],
    mode: str,
    goals: list[dict],
) -> Generator[str, None, None]:
    """Route user message through tools if needed, then stream LLM response."""
    user_message = messages[-1]["content"] if messages else ""
    logger.info("Orchestrating response for: %r", user_message[:100])

    # Step 1: Check if any tools should be called
    tool_outputs = route_and_call_tools(user_message)

    # Step 2: Format tool results as context for the LLM
    tool_context = ""
    if tool_outputs:
        lines = []
        for output in tool_outputs:
            # raw_input is {'args': ('phrase',), 'kwargs': {}}
            phrase = output.raw_input.get("args", ("",))[0]
            lines.append(f"{output.tool_name}: \"{phrase}\" → \"{output.content}\"")
        tool_context = "\n".join(lines)
        logger.info("Tool context: %s", tool_context)

    # Step 3: Stream LLM response with tool results injected
    yield from llm_stream(messages, mode, goals, tool_context)
