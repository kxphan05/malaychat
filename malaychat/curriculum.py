"""Structured curriculum for Malay language learning."""

from __future__ import annotations

CURRICULUM: list[dict] = [
    {
        "level": 1,
        "title": "Foundations",
        "lessons": [
            {
                "id": "1.1",
                "title": "Greetings & Introductions",
                "description": "Learn to greet people and introduce yourself",
                "vocabulary": [
                    {"malay": "Selamat pagi", "english": "Good morning"},
                    {"malay": "Selamat tengah hari", "english": "Good afternoon"},
                    {"malay": "Selamat petang", "english": "Good evening"},
                    {"malay": "Selamat malam", "english": "Good night"},
                    {"malay": "Apa khabar?", "english": "How are you?"},
                    {"malay": "Khabar baik", "english": "I'm fine"},
                    {"malay": "Nama saya", "english": "My name is"},
                    {"malay": "Siapa nama awak?", "english": "What is your name?"},
                    {"malay": "Selamat tinggal", "english": "Goodbye (said by the one leaving)"},
                    {"malay": "Selamat jalan", "english": "Goodbye (said by the one staying)"},
                    {"malay": "Jumpa lagi", "english": "See you again"},
                    {"malay": "Saya dari", "english": "I am from"},
                ],
                "practice_prompts": [
                    "Teach me how to greet someone in the morning",
                    "How do I introduce myself in Malay?",
                    "Let's role-play: I'm meeting you for the first time",
                    "What's the difference between selamat tinggal and selamat jalan?",
                    "How do I ask someone how they are?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "1.2",
                "title": "Numbers & Counting",
                "description": "Learn numbers 1-20 and basic counting",
                "vocabulary": [
                    {"malay": "satu", "english": "one"},
                    {"malay": "dua", "english": "two"},
                    {"malay": "tiga", "english": "three"},
                    {"malay": "empat", "english": "four"},
                    {"malay": "lima", "english": "five"},
                    {"malay": "enam", "english": "six"},
                    {"malay": "tujuh", "english": "seven"},
                    {"malay": "lapan", "english": "eight"},
                    {"malay": "sembilan", "english": "nine"},
                    {"malay": "sepuluh", "english": "ten"},
                    {"malay": "sebelas", "english": "eleven"},
                    {"malay": "dua belas", "english": "twelve"},
                ],
                "practice_prompts": [
                    "Teach me numbers 1 to 10 in Malay",
                    "How do I count from 11 to 20?",
                    "Quiz me on Malay numbers",
                    "How do I say prices using numbers?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 8,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "1.3",
                "title": "Polite Expressions",
                "description": "Learn essential polite phrases for daily interactions",
                "vocabulary": [
                    {"malay": "Terima kasih", "english": "Thank you"},
                    {"malay": "Sama-sama", "english": "You're welcome"},
                    {"malay": "Maaf", "english": "Sorry"},
                    {"malay": "Tumpang tanya", "english": "Excuse me (to ask a question)"},
                    {"malay": "Tolong", "english": "Please / Help"},
                    {"malay": "Sila", "english": "Please (formal invitation)"},
                    {"malay": "Tidak apa", "english": "It's okay / Never mind"},
                    {"malay": "Minta maaf", "english": "I apologize"},
                    {"malay": "Boleh", "english": "Can / May"},
                    {"malay": "Tidak boleh", "english": "Cannot / May not"},
                ],
                "practice_prompts": [
                    "How do I say thank you in Malay?",
                    "Teach me how to apologize politely",
                    "How do I politely ask for help?",
                    "Let's practice using polite expressions in a conversation",
                    "What's the difference between maaf and minta maaf?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
        ],
    },
    {
        "level": 2,
        "title": "Daily Life",
        "lessons": [
            {
                "id": "2.1",
                "title": "Ordering Food & Drinks",
                "description": "Learn to order at restaurants and food stalls",
                "vocabulary": [
                    {"malay": "Saya nak", "english": "I want"},
                    {"malay": "Makan", "english": "Eat"},
                    {"malay": "Minum", "english": "Drink"},
                    {"malay": "Nasi", "english": "Rice"},
                    {"malay": "Air", "english": "Water / Drink"},
                    {"malay": "Pedas", "english": "Spicy"},
                    {"malay": "Tidak pedas", "english": "Not spicy"},
                    {"malay": "Sedap", "english": "Delicious"},
                    {"malay": "Menu", "english": "Menu"},
                    {"malay": "Bil", "english": "Bill"},
                    {"malay": "Meja", "english": "Table"},
                    {"malay": "Satu lagi", "english": "One more"},
                ],
                "practice_prompts": [
                    "How do I order food in Malay?",
                    "Let's role-play: I'm ordering at a mamak stall",
                    "How do I ask for the bill?",
                    "How do I say 'not spicy' in Malay?",
                    "Teach me common food vocabulary",
                ],
                "completion_criteria": {
                    "vocab_practiced": 7,
                    "messages_exchanged": 10,
                },
            },
            {
                "id": "2.2",
                "title": "Shopping & Prices",
                "description": "Learn to shop and negotiate at markets",
                "vocabulary": [
                    {"malay": "Berapa harga?", "english": "How much?"},
                    {"malay": "Mahal", "english": "Expensive"},
                    {"malay": "Murah", "english": "Cheap"},
                    {"malay": "Boleh kurang?", "english": "Can you reduce?"},
                    {"malay": "Saya nak beli", "english": "I want to buy"},
                    {"malay": "Ringgit", "english": "Ringgit (currency)"},
                    {"malay": "Sen", "english": "Cent"},
                    {"malay": "Berapa semua?", "english": "How much for all?"},
                    {"malay": "Bagi diskaun", "english": "Give a discount"},
                    {"malay": "Saya ambil ini", "english": "I'll take this"},
                ],
                "practice_prompts": [
                    "How do I ask 'how much?' in Malay?",
                    "Teach me bargaining phrases",
                    "Let's role-play: I'm shopping at Pasar Seni",
                    "How do I say 'too expensive' in Malay?",
                    "How do I say 'I'll take this'?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 10,
                },
            },
            {
                "id": "2.3",
                "title": "Asking for Directions",
                "description": "Learn to ask for and understand directions",
                "vocabulary": [
                    {"malay": "Di mana", "english": "Where"},
                    {"malay": "Kiri", "english": "Left"},
                    {"malay": "Kanan", "english": "Right"},
                    {"malay": "Terus", "english": "Straight"},
                    {"malay": "Dekat", "english": "Near"},
                    {"malay": "Jauh", "english": "Far"},
                    {"malay": "Belakang", "english": "Behind"},
                    {"malay": "Depan", "english": "In front"},
                    {"malay": "Sebelah", "english": "Next to / Beside"},
                    {"malay": "Tandas", "english": "Toilet"},
                ],
                "practice_prompts": [
                    "How do I ask for directions in Malay?",
                    "How do I say 'where is the toilet?'",
                    "Teach me left, right, straight in Malay",
                    "Let's role-play: I'm lost and asking a stranger for help",
                    "How do I ask 'is it far?' in Malay?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "2.4",
                "title": "Transport & Getting Around",
                "description": "Learn to use taxis, buses, and navigate transport",
                "vocabulary": [
                    {"malay": "Teksi", "english": "Taxi"},
                    {"malay": "Bas", "english": "Bus"},
                    {"malay": "Kereta", "english": "Car"},
                    {"malay": "Stesen", "english": "Station"},
                    {"malay": "Berhenti", "english": "Stop"},
                    {"malay": "Pergi ke", "english": "Go to"},
                    {"malay": "Berapa tambang?", "english": "How much is the fare?"},
                    {"malay": "Berhenti sini", "english": "Stop here"},
                    {"malay": "Naik", "english": "Board / Get on"},
                    {"malay": "Turun", "english": "Alight / Get off"},
                ],
                "practice_prompts": [
                    "How do I take a taxi in Malay?",
                    "How do I say 'stop here'?",
                    "Let's role-play: I'm taking a Grab to KLCC",
                    "How do I ask about the fare?",
                    "Teach me transport words in Malay",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
        ],
    },
    {
        "level": 3,
        "title": "Conversations",
        "lessons": [
            {
                "id": "3.1",
                "title": "Talking About Family",
                "description": "Learn family vocabulary and how to talk about relatives",
                "vocabulary": [
                    {"malay": "Keluarga", "english": "Family"},
                    {"malay": "Ibu", "english": "Mother"},
                    {"malay": "Ayah / Bapa", "english": "Father"},
                    {"malay": "Abang", "english": "Older brother"},
                    {"malay": "Kakak", "english": "Older sister"},
                    {"malay": "Adik", "english": "Younger sibling"},
                    {"malay": "Anak", "english": "Child / Son / Daughter"},
                    {"malay": "Suami", "english": "Husband"},
                    {"malay": "Isteri", "english": "Wife"},
                    {"malay": "Datuk", "english": "Grandfather"},
                    {"malay": "Nenek", "english": "Grandmother"},
                ],
                "practice_prompts": [
                    "Teach me family words in Malay",
                    "How do I introduce my family?",
                    "Let's role-play: Tell me about your family",
                    "How do I say 'older brother' vs 'younger brother'?",
                    "How do I talk about my family in Malay?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "3.2",
                "title": "Weather & Small Talk",
                "description": "Learn to make small talk about weather and daily life",
                "vocabulary": [
                    {"malay": "Cuaca", "english": "Weather"},
                    {"malay": "Panas", "english": "Hot"},
                    {"malay": "Sejuk", "english": "Cold"},
                    {"malay": "Hujan", "english": "Rain"},
                    {"malay": "Cerah", "english": "Sunny / Clear"},
                    {"malay": "Mendung", "english": "Cloudy"},
                    {"malay": "Hari ini", "english": "Today"},
                    {"malay": "Esok", "english": "Tomorrow"},
                    {"malay": "Semalam", "english": "Yesterday"},
                    {"malay": "Bagaimana", "english": "How"},
                ],
                "practice_prompts": [
                    "How do I talk about the weather in Malay?",
                    "How do I say 'it's raining' in Malay?",
                    "Let's have a casual conversation about our day",
                    "How do I make small talk in Malay?",
                    "Teach me words for today, tomorrow, yesterday",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "3.3",
                "title": "At the Hotel",
                "description": "Learn to check in, ask about amenities, and handle hotel situations",
                "vocabulary": [
                    {"malay": "Bilik", "english": "Room"},
                    {"malay": "Kunci", "english": "Key"},
                    {"malay": "Daftar masuk", "english": "Check in"},
                    {"malay": "Daftar keluar", "english": "Check out"},
                    {"malay": "Satu malam", "english": "One night"},
                    {"malay": "Tuala", "english": "Towel"},
                    {"malay": "Katil", "english": "Bed"},
                    {"malay": "Tingkat", "english": "Floor / Level"},
                    {"malay": "Sarapan", "english": "Breakfast"},
                    {"malay": "Kata laluan wifi", "english": "Wifi password"},
                ],
                "practice_prompts": [
                    "How do I check in at a hotel in Malay?",
                    "Let's role-play: I'm checking into a hotel",
                    "How do I ask for the wifi password?",
                    "How do I request extra towels?",
                    "How do I ask about breakfast?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
            {
                "id": "3.4",
                "title": "Emergencies & Health",
                "description": "Learn essential phrases for emergencies and health situations",
                "vocabulary": [
                    {"malay": "Tolong!", "english": "Help!"},
                    {"malay": "Sakit", "english": "Sick / Pain"},
                    {"malay": "Doktor", "english": "Doctor"},
                    {"malay": "Hospital", "english": "Hospital"},
                    {"malay": "Polis", "english": "Police"},
                    {"malay": "Ambulans", "english": "Ambulance"},
                    {"malay": "Ubat", "english": "Medicine"},
                    {"malay": "Demam", "english": "Fever"},
                    {"malay": "Farmasi", "english": "Pharmacy"},
                    {"malay": "Kecemasan", "english": "Emergency"},
                ],
                "practice_prompts": [
                    "How do I say 'I need help' in Malay?",
                    "How do I ask for a doctor?",
                    "Let's role-play: I'm at a pharmacy explaining my symptoms",
                    "Teach me emergency phrases in Malay",
                    "How do I say 'I'm not feeling well'?",
                ],
                "completion_criteria": {
                    "vocab_practiced": 6,
                    "messages_exchanged": 8,
                },
            },
        ],
    },
]

# Build a flat lookup for quick access by lesson ID
_LESSON_INDEX: dict[str, dict] = {}
for _level in CURRICULUM:
    for _lesson in _level["lessons"]:
        _LESSON_INDEX[_lesson["id"]] = _lesson

# Ordered list of all lesson IDs
ALL_LESSON_IDS: list[str] = [
    lesson["id"]
    for level in CURRICULUM
    for lesson in level["lessons"]
]


def get_all_levels() -> list[dict]:
    """Return the full curriculum structure."""
    return CURRICULUM


def get_lesson(lesson_id: str) -> dict | None:
    """Return a single lesson by ID, or None if not found."""
    return _LESSON_INDEX.get(lesson_id)


def get_lesson_vocabulary(lesson_id: str) -> list[dict]:
    """Return the vocabulary list for a lesson."""
    lesson = get_lesson(lesson_id)
    if lesson is None:
        return []
    return lesson["vocabulary"]


def get_lesson_prompts(lesson_id: str) -> list[str]:
    """Return the practice prompts for a lesson."""
    lesson = get_lesson(lesson_id)
    if lesson is None:
        return []
    return lesson["practice_prompts"]


def get_next_lesson(current_lesson_id: str, completed_lessons: list[str]) -> str | None:
    """Return the ID of the next uncompleted lesson, or None if all are done."""
    try:
        current_idx = ALL_LESSON_IDS.index(current_lesson_id)
    except ValueError:
        current_idx = -1

    # Look forward from the current position
    for lesson_id in ALL_LESSON_IDS[current_idx + 1:]:
        if lesson_id not in completed_lessons:
            return lesson_id

    # Wrap around: check lessons before the current one
    for lesson_id in ALL_LESSON_IDS[:current_idx + 1]:
        if lesson_id not in completed_lessons:
            return lesson_id

    return None


def get_level_for_lesson(lesson_id: str) -> dict | None:
    """Return the level that contains the given lesson."""
    for level in CURRICULUM:
        for lesson in level["lessons"]:
            if lesson["id"] == lesson_id:
                return level
    return None


def format_vocab_reference(lesson_id: str) -> str:
    """Format lesson vocabulary as a compact reference string."""
    vocab = get_lesson_vocabulary(lesson_id)
    if not vocab:
        return ""
    lines = [f"- **{v['malay']}** — {v['english']}" for v in vocab]
    return "\n".join(lines)
