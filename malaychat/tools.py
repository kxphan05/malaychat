"""Translation tool definitions and routing logic."""

import logging
import re
from dataclasses import dataclass
from typing import Callable

from malaychat.translator import to_english, to_malay

logger = logging.getLogger("malaychat.tools")


# --- Simple tool wrapper (replaces LlamaIndex FunctionTool) ---

@dataclass
class ToolOutput:
    """Result of a tool call."""
    tool_name: str
    input_phrase: str
    content: str


@dataclass
class Tool:
    """A callable tool with a name and description."""
    name: str
    description: str
    fn: Callable[[str], str]

    def call(self, phrase: str) -> ToolOutput:
        result = self.fn(phrase)
        return ToolOutput(tool_name=self.name, input_phrase=phrase, content=result)


# --- Tool definitions ---

translate_to_malay_tool = Tool(
    name="translate_to_malay",
    description="Translates an English word or phrase to Malay (Bahasa Melayu).",
    fn=to_malay,
)

translate_to_english_tool = Tool(
    name="translate_to_english",
    description="Translates a Malay word or phrase to English.",
    fn=to_english,
)

ALL_TOOLS = [translate_to_malay_tool, translate_to_english_tool]

# --- Patterns that signal translation is needed ---

_TO_MALAY_PATTERNS = [
    re.compile(r"how (?:do (?:I|you)|to) say\b", re.IGNORECASE),
    re.compile(r"what(?:'s| is) .+ in malay", re.IGNORECASE),
    re.compile(r"\btranslate\b.+(?:to|into)?\s*malay", re.IGNORECASE),
    re.compile(r"\btranslate\b", re.IGNORECASE),
    re.compile(r"\bin malay\b", re.IGNORECASE),
    re.compile(r"how (?:do (?:I|you)|to) (?:ask|order|greet|bargain|negotiate|request|say)", re.IGNORECASE),
    re.compile(r"(?:teach|tell|show) me .+ in malay", re.IGNORECASE),
    re.compile(r"malay (?:word|phrase|translation|equivalent) for", re.IGNORECASE),
]

_TO_ENGLISH_PATTERNS = [
    re.compile(r"what does .+ mean", re.IGNORECASE),
    re.compile(r"what is the meaning of", re.IGNORECASE),
    re.compile(r"\btranslate\b.+(?:to|into)?\s*english", re.IGNORECASE),
    re.compile(r"\bin english\b", re.IGNORECASE),
]


def _extract_phrase(text: str) -> str:
    """Extract the phrase the user wants translated."""
    # Quoted phrases first
    quoted = re.findall(r"['\"](.+?)['\"]", text)
    if quoted:
        return quoted[0]

    # "how do I say X in malay"
    m = re.search(
        r"(?:how (?:do I|to) say|translate)\s+(.+?)(?:\s+(?:in|to|into)\s+(?:malay|english))?[?.!]?\s*$",
        text, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().strip("'\"")

    # "what is X in malay"
    m = re.search(r"what(?:'s| is)\s+(.+?)\s+in\s+malay", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip("'\"")

    # "what does X mean"
    m = re.search(r"what does\s+(.+?)\s+mean", text, re.IGNORECASE)
    if m:
        return m.group(1).strip().strip("'\"")

    return text


def route_and_call_tools(user_message: str) -> list[ToolOutput]:
    """Decide which tools to call based on the user message, then call them."""
    results: list[ToolOutput] = []
    phrase = _extract_phrase(user_message)

    # Check if we should translate to Malay
    for pattern in _TO_MALAY_PATTERNS:
        if pattern.search(user_message):
            logger.info("Routing to translate_to_malay: %r", phrase)
            output = translate_to_malay_tool.call(phrase)
            logger.info("Tool result: %s -> %s", output.input_phrase, output.content)
            results.append(output)
            return results

    # Check if we should translate to English
    for pattern in _TO_ENGLISH_PATTERNS:
        if pattern.search(user_message):
            logger.info("Routing to translate_to_english: %r", phrase)
            output = translate_to_english_tool.call(phrase)
            logger.info("Tool result: %s -> %s", output.input_phrase, output.content)
            results.append(output)
            return results

    logger.info("No tool call needed for: %r", user_message[:80])
    return results
