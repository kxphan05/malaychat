"""Recommended prompts system based on user goals and conversation context."""

import re

# Goal category keywords → recommended prompts
_GOAL_PROMPTS: dict[str, list[str]] = {
    "greetings": [
        "How do I say hello in Malay?",
        "Teach me formal vs informal greetings",
        "How do I greet someone in the morning?",
        "How do I say goodbye in Malay?",
        "How do I introduce myself in Malay?",
    ],
    "food": [
        "How do I order food in Malay?",
        "How do I say 'I want nasi lemak' in Malay?",
        "What are common food words in Malay?",
        "How do I ask for the menu?",
        "How do I say 'no spicy' in Malay?",
    ],
    "marketplace": [
        "How do I ask 'how much?' in Malay?",
        "Teach me bargaining phrases",
        "How do I say 'too expensive' in Malay?",
        "How do I ask for a discount?",
        "How do I say 'I want to buy this'?",
    ],
    "numbers": [
        "Teach me numbers 1 to 10 in Malay",
        "How do I count in Malay?",
        "How do I say prices in Malay?",
        "What is 'one hundred' in Malay?",
    ],
    "directions": [
        "How do I ask for directions in Malay?",
        "How do I say 'where is the toilet?'",
        "Teach me left, right, straight in Malay",
        "How do I ask 'how far?' in Malay?",
    ],
    "transport": [
        "How do I take a taxi in Malay?",
        "How do I ask 'how much to go to...?'",
        "Teach me transport words in Malay",
        "How do I say 'stop here' in Malay?",
    ],
    "polite": [
        "How do I say thank you in Malay?",
        "How do I say sorry in Malay?",
        "Teach me polite expressions in Malay",
        "How do I say 'excuse me' in Malay?",
    ],
    "weather": [
        "How do I talk about weather in Malay?",
        "How do I say 'it's raining' in Malay?",
        "What does 'panas' mean?",
    ],
    "family": [
        "Teach me family words in Malay",
        "How do I say 'mother' and 'father' in Malay?",
        "How do I talk about my family in Malay?",
    ],
    "time": [
        "How do I ask 'what time is it?' in Malay?",
        "Teach me days of the week in Malay",
        "How do I say 'tomorrow' in Malay?",
    ],
    "hotel": [
        "How do I check in at a hotel in Malay?",
        "How do I ask for a room?",
        "How do I ask about the wifi password?",
    ],
    "emergency": [
        "Teach me emergency phrases in Malay",
        "How do I say 'I need help' in Malay?",
        "How do I ask for a doctor in Malay?",
    ],
}

# Keywords that map to each category
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "greetings": ["greet", "hello", "hi", "introduce", "introduction", "meet"],
    "food": ["food", "eat", "restaurant", "order", "drink", "meal", "cook", "menu", "dining"],
    "marketplace": ["market", "shop", "buy", "bargain", "price", "sell", "store", "shopping", "haggle"],
    "numbers": ["number", "count", "digit", "math"],
    "directions": ["direction", "navigate", "place", "location", "map", "way", "where"],
    "transport": ["transport", "taxi", "bus", "train", "drive", "travel", "ride", "grab"],
    "polite": ["polite", "thank", "sorry", "excuse", "manner", "courtesy", "please", "formal"],
    "weather": ["weather", "rain", "hot", "cold", "sun", "climate"],
    "family": ["family", "mother", "father", "parent", "sibling", "brother", "sister", "relative"],
    "time": ["time", "day", "week", "month", "clock", "schedule", "date", "hour"],
    "hotel": ["hotel", "stay", "room", "accommodation", "check-in", "booking"],
    "emergency": ["emergency", "help", "doctor", "hospital", "police", "urgent", "sick"],
}

# Fallback prompts when no goals match or no goals set
_DEFAULT_PROMPTS = [
    "How do I say hello in Malay?",
    "Teach me basic greetings",
    "How do I order food in Malay?",
    "How do I say thank you?",
    "Teach me numbers 1 to 10",
]

# Prompts for freeform chat mode
_CHAT_PROMPTS = [
    "Apa khabar? How's your day going?",
    "Let's practice ordering food in Malay",
    "Can we have a conversation at a market?",
    "Let's role-play meeting someone new",
    "Quiz me on Malay words I've learned",
]

# Follow-up prompts by topic detected in recent messages
_FOLLOWUP_KEYWORDS: dict[str, list[str]] = {
    "greetings": [
        "Now teach me how to reply to greetings",
        "How do I greet someone older than me?",
        "What about informal greetings?",
    ],
    "food": [
        "How do I ask for the bill?",
        "How do I say 'delicious' in Malay?",
        "Teach me more food vocabulary",
    ],
    "marketplace": [
        "How do I say 'can you lower the price?'",
        "Teach me more shopping phrases",
        "How do I say 'I'll take it'?",
    ],
    "numbers": [
        "Now teach me 11 to 20",
        "How do I use numbers when shopping?",
        "Teach me ordinal numbers in Malay",
    ],
    "polite": [
        "How do I say 'you're welcome'?",
        "Teach me more polite expressions",
        "How do I apologize formally?",
    ],
}


def _classify_goal(goal_text: str) -> list[str]:
    """Classify a goal into categories based on keyword matching."""
    text_lower = goal_text.lower()
    categories = []
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(category)
    return categories


def _detect_recent_topics(messages: list[dict], lookback: int = 4) -> list[str]:
    """Detect topics discussed in recent messages."""
    recent = messages[-lookback:] if messages else []
    combined = " ".join(m["content"].lower() for m in recent)
    topics = []
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            topics.append(category)
    return topics


def _already_asked(prompt: str, messages: list[dict]) -> bool:
    """Check if a prompt (or something very similar) was already asked."""
    if not messages:
        return False
    prompt_words = set(re.findall(r"\b\w{4,}\b", prompt.lower()))
    for msg in messages:
        if msg["role"] != "user":
            continue
        msg_words = set(re.findall(r"\b\w{4,}\b", msg["content"].lower()))
        # If most of the prompt words appear in a previous message, skip it
        if len(prompt_words) > 0 and len(prompt_words & msg_words) / len(prompt_words) >= 0.6:
            return True
    return False


def get_recommended_prompts(
    goals: list[dict],
    messages: list[dict],
    mode: str,
    max_prompts: int = 3,
) -> list[str]:
    """
    Generate recommended prompts based on goals, conversation history, and mode.

    Returns up to max_prompts suggestions that haven't been asked yet.
    """
    candidates: list[str] = []

    if mode == "Chat":
        # Chat mode: suggest freeform conversation starters
        candidates.extend(_CHAT_PROMPTS)
        # Also add follow-ups based on recent topics
        for topic in _detect_recent_topics(messages):
            candidates.extend(_FOLLOWUP_KEYWORDS.get(topic, []))
    else:
        # Learning mode: prioritize goal-aligned prompts
        active_goals = [g for g in goals if not g["completed"]]

        if active_goals:
            # Gather prompts matching active goals
            for goal in active_goals:
                categories = _classify_goal(goal["text"])
                for cat in categories:
                    candidates.extend(_GOAL_PROMPTS.get(cat, []))

            # If conversation has history, also suggest follow-ups
            if messages:
                for topic in _detect_recent_topics(messages):
                    candidates.extend(_FOLLOWUP_KEYWORDS.get(topic, []))

            # If no categories matched, add generic prompts from goal text
            if not candidates:
                for goal in active_goals:
                    candidates.append(f"Help me with: {goal['text']}")
        else:
            # No active goals: use defaults
            candidates.extend(_DEFAULT_PROMPTS)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    # Filter out prompts similar to what's already been asked
    filtered = [p for p in unique if not _already_asked(p, messages)]

    # If everything was filtered, fall back to defaults
    if not filtered:
        filtered = [p for p in _DEFAULT_PROMPTS if not _already_asked(p, messages)]

    return filtered[:max_prompts]
