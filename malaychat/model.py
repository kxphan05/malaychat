"""Orchestrator: routes to tools, then streams LLM response."""

import logging
from collections.abc import Generator

from malaychat.llm import stream_response as llm_stream
from malaychat.tools import ToolOutput, route_and_call_tools

logger = logging.getLogger("malaychat.model")


def get_tool_results(user_message: str) -> list[ToolOutput]:
    """Check if any tools should be called and return results."""
    return route_and_call_tools(user_message)


def stream_response(
    messages: list[dict],
    mode: str,
    goals: list[dict],
    tool_outputs: list[ToolOutput],
    roleplay: bool = False,
    active_lesson_id: str | None = None,
) -> Generator[str, None, None]:
    """Stream LLM response with tool results injected as context."""
    tool_context = ""
    if tool_outputs:
        lines = []
        for output in tool_outputs:
            lines.append(f"{output.tool_name}: \"{output.input_phrase}\" → \"{output.content}\"")
        tool_context = "\n".join(lines)
        logger.info("Tool context: %s", tool_context)

    yield from llm_stream(messages, mode, goals, tool_context, roleplay, active_lesson_id)
