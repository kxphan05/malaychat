"""Main Streamlit chat interface for MalayChat."""

import logging

import streamlit as st

logger = logging.getLogger("malaychat.chat")

from malaychat.auth import render_login
from malaychat.curriculum import (
    ALL_LESSON_IDS,
    format_vocab_reference,
    get_all_levels,
    get_lesson,
    get_lesson_vocabulary,
    get_next_lesson,
)
from malaychat.goals import (
    add_goal,
    check_goal_completion,
    get_goals,
    init_goals,
    remove_goal,
    toggle_goal,
)
from malaychat.model import get_tool_results, stream_response
from malaychat.progress import (
    check_lesson_completion,
    complete_lesson,
    extract_vocabulary,
    load_progress,
    record_session,
    record_vocab,
    save_progress,
)
from malaychat.prompts import get_recommended_prompts

WELCOME_MSG = (
    "Selamat datang! Welcome to MalayChat! 🇲🇾\n\n"
    "I'm your Malay language learning companion. "
    "You can practice conversational Malay with me in two modes:\n\n"
    "- **Learning Mode**: Set goals in the sidebar and I'll help you achieve them\n"
    "- **Chat Mode**: Have a freeform conversation to practice your Malay\n\n"
    "Try adding a goal like *\"Learn 3 marketplace phrases\"* in the sidebar, "
    "or just start chatting!"
)


def _init_lesson_state() -> None:
    """Initialize lesson-related session state from persisted progress."""
    if "progress_loaded" not in st.session_state:
        progress = load_progress()
        st.session_state.progress = progress
        st.session_state.active_lesson = progress.get("current_lesson")
        st.session_state.completed_lessons = progress.get("completed_lessons", [])
        st.session_state.progress_loaded = True
    if "active_lesson" not in st.session_state:
        st.session_state.active_lesson = None
    if "completed_lessons" not in st.session_state:
        st.session_state.completed_lessons = []


def _render_lesson_panel() -> None:
    """Render the lesson selector and vocabulary reference in the sidebar."""
    st.subheader("Lessons")

    levels = get_all_levels()
    active_id = st.session_state.active_lesson
    completed = st.session_state.completed_lessons

    for level in levels:
        # Count completed lessons in this level
        level_lessons = level["lessons"]
        done_count = sum(1 for l in level_lessons if l["id"] in completed)
        label = f"Level {level['level']}: {level['title']} ({done_count}/{len(level_lessons)})"

        with st.expander(label, expanded=(active_id is not None and any(l["id"] == active_id for l in level_lessons))):
            for lesson in level_lessons:
                lid = lesson["id"]
                is_active = lid == active_id
                is_done = lid in completed

                # Status prefix
                if is_done:
                    prefix = "✅"
                elif is_active:
                    prefix = "▶️"
                else:
                    prefix = "⬜"

                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    style = "~~" if is_done else ("**" if is_active else "")
                    st.markdown(f"{prefix} {style}{lid} {lesson['title']}{style}")
                with col2:
                    if not is_active:
                        if st.button("Go", key=f"lesson_{lid}"):
                            st.session_state.active_lesson = lid
                            st.session_state.progress["current_lesson"] = lid
                            save_progress(st.session_state.progress)
                            st.rerun()

    # Active lesson details
    if active_id:
        lesson = get_lesson(active_id)
        if lesson:
            st.divider()
            st.markdown(f"**Current: {lesson['title']}**")
            st.caption(lesson["description"])

            # Vocabulary reference card
            with st.expander("Vocabulary", expanded=True):
                vocab_ref = format_vocab_reference(active_id)
                st.markdown(vocab_ref)

            # Next lesson button
            next_id = get_next_lesson(active_id, completed)
            col_prev, col_next = st.columns(2)
            with col_prev:
                # Find previous lesson
                try:
                    idx = ALL_LESSON_IDS.index(active_id)
                except ValueError:
                    idx = 0
                if idx > 0:
                    if st.button("← Previous", use_container_width=True):
                        st.session_state.active_lesson = ALL_LESSON_IDS[idx - 1]
                        st.rerun()
            with col_next:
                if next_id and next_id != active_id:
                    if st.button("Next →", use_container_width=True):
                        st.session_state.active_lesson = next_id
                        st.rerun()

            if st.button("Exit Lesson", use_container_width=True):
                st.session_state.active_lesson = None
                # Sync to progress
                st.session_state.progress["current_lesson"] = ""
                save_progress(st.session_state.progress)
                st.rerun()
    else:
        st.caption("Select a lesson to start structured learning.")


def render_sidebar() -> str:
    """Render the sidebar with mode toggle and goal management. Returns current mode."""
    with st.sidebar:
        st.header("MalayChat")

        # User info + logout
        col_user, col_logout = st.columns([0.65, 0.35])
        with col_user:
            st.caption(f"Logged in as **{st.session_state.username}**")
        with col_logout:
            if st.button("Log out", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        mode = st.radio(
            "Mode",
            ["Learning", "Chat"],
            horizontal=True,
            help="Learning Mode helps you work toward goals. Chat Mode is freeform practice.",
        )

        if mode == "Learning":
            st.divider()
            _render_lesson_panel()

        st.divider()
        st.subheader("Learning Goals")

        # Goal input
        new_goal = st.text_input(
            "Add a goal",
            placeholder="e.g. Learn 3 marketplace phrases",
            key="goal_input",
        )
        if st.button("Add Goal", use_container_width=True) and new_goal:
            add_goal(new_goal)
            st.rerun()

        # Display goals
        goals = get_goals()
        if goals:
            for i, goal in enumerate(goals):
                col1, col2, col3 = st.columns([0.1, 0.75, 0.15])
                with col1:
                    if goal["completed"]:
                        st.markdown("✅")
                    else:
                        st.markdown("⬜")
                with col2:
                    style = "~~" if goal["completed"] else ""
                    st.markdown(f"{style}{goal['text']}{style}")
                with col3:
                    if st.button("✕", key=f"del_{i}"):
                        remove_goal(i)
                        st.rerun()
        else:
            st.caption(
                "No goals yet. Try adding:\n"
                '- "Learn greetings"\n'
                '- "Learn to order food"\n'
                '- "Learn marketplace phrases"'
            )

        st.divider()

        # Stats
        if goals:
            completed = sum(1 for g in goals if g["completed"])
            st.metric("Goals Completed", f"{completed}/{len(goals)}")

        # Progress dashboard
        if "progress" in st.session_state:
            st.divider()
            st.subheader("Progress")
            progress = st.session_state.progress
            stats = progress.get("stats", {})

            # Streak
            streak = stats.get("current_streak_days", 0)
            if streak > 0:
                st.markdown(f"**{streak}-day streak**")
            else:
                st.caption("Start your streak today!")

            # Level progress
            for level in get_all_levels():
                level_lessons = level["lessons"]
                done = sum(1 for l in level_lessons if l["id"] in progress.get("completed_lessons", []))
                total = len(level_lessons)
                st.progress(done / total if total > 0 else 0, text=f"Level {level['level']}: {done}/{total}")

            # Summary stats
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Vocab Learned", stats.get("total_vocab_learned", 0))
            with col_s2:
                st.metric("Sessions", stats.get("total_sessions", 0))

            # Vocabulary journal
            vocab = progress.get("vocabulary", {})
            if vocab:
                with st.expander("Vocabulary Journal"):
                    for word, info in sorted(vocab.items(), key=lambda x: x[1].get("last_seen", ""), reverse=True):
                        st.markdown(f"**{word}** — {info['english']}  ×{info['times_seen']}")

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    return mode


def run() -> None:
    """Main app entry point."""
    st.set_page_config(
        page_title="MalayChat",
        page_icon="🇲🇾",
        layout="centered",
    )

    # Login gate — must authenticate before using the app
    username = render_login()
    if username is None:
        return

    # Initialize state
    init_goals()
    _init_lesson_state()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    mode = render_sidebar()

    # Initialize roleplay state
    if "roleplay" not in st.session_state:
        st.session_state.roleplay = False

    # Title
    st.title("MalayChat 🇲🇾")
    active_lesson = None
    if mode == "Learning" and st.session_state.active_lesson:
        active_lesson = get_lesson(st.session_state.active_lesson)
    if active_lesson:
        mode_desc = f"Lesson {active_lesson['id']}: {active_lesson['title']}"
    elif mode == "Learning":
        mode_desc = "Work toward your learning goals"
    else:
        mode_desc = "Freeform Malay conversation practice"
    if st.session_state.roleplay:
        mode_desc += " (Role-play active)"
    st.caption(f"Mode: **{mode}** — {mode_desc}")

    # Display welcome message if no history
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            if active_lesson:
                lesson_welcome = (
                    f"Let's start **Lesson {active_lesson['id']}: {active_lesson['title']}**!\n\n"
                    f"{active_lesson['description']}.\n\n"
                    "Pick a prompt below or ask me anything about this topic!"
                )
                st.markdown(lesson_welcome)
            else:
                st.markdown(WELCOME_MSG)

    # Render message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Role-play toggle (right-aligned, above prompts/input)
    col_spacer, col_rp = st.columns([0.8, 0.2])
    with col_rp:
        roleplay_on = st.toggle("Role-play", value=st.session_state.roleplay, key="roleplay_toggle")
        if roleplay_on != st.session_state.roleplay:
            st.session_state.roleplay = roleplay_on
            st.rerun()

    # Recommended prompts
    suggestions = get_recommended_prompts(
        get_goals(), st.session_state.messages, mode,
        active_lesson_id=st.session_state.active_lesson,
    )
    if suggestions:
        cols = st.columns(len(suggestions))
        for i, (col, suggestion) in enumerate(zip(cols, suggestions)):
            with col:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.pending_prompt = suggestion
                    st.rerun()

    # Always render chat input so the box is visible
    chat_input = st.chat_input("Type your message...")

    # Pending prompt from suggestion button takes priority
    user_input = None
    if "pending_prompt" in st.session_state:
        user_input = st.session_state.pending_prompt
        del st.session_state.pending_prompt
    elif chat_input:
        user_input = chat_input

    # Process input
    if user_input:
        logger.info("User input received: %r", user_input[:100])

        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Step 1: Check for tool calls
        tool_outputs = get_tool_results(user_input)

        # Show tool calls in the UI
        if tool_outputs:
            for output in tool_outputs:
                tool_label = "Translating to Malay" if "malay" in output.tool_name else "Translating to English"
                with st.status(f"{tool_label}...", state="complete"):
                    st.code(f"{output.tool_name}(\"{output.input_phrase}\")", language=None)
                    st.markdown(f"**Result:** {output.content}")

        # Step 2: Stream LLM response with tool results
        with st.chat_message("assistant"):
            try:
                token_stream = stream_response(
                    st.session_state.messages,
                    mode,
                    get_goals(),
                    tool_outputs,
                    roleplay=st.session_state.roleplay,
                    active_lesson_id=st.session_state.active_lesson,
                )
                response = st.write_stream(token_stream)
                logger.info("Streamed response (%d chars): %r", len(response), response[:100])
            except Exception:
                logger.exception("stream_response failed")
                response = "Sorry, something went wrong. Check the terminal logs for details."
                st.error(response)

            if not response:
                logger.warning("Response was empty")
                st.warning("The model returned an empty response. Check the terminal logs.")

        st.session_state.messages.append({"role": "assistant", "content": response})

        # Check goal completion in learning mode
        if mode == "Learning":
            completed_indices = check_goal_completion(response)
            if completed_indices:
                goals = get_goals()
                names = [goals[i]["text"] for i in completed_indices]
                st.toast(f"Goal completed: {', '.join(names)}", icon="✅")

        # Track vocabulary and lesson progress
        lesson_id = st.session_state.active_lesson
        if lesson_id and response and "progress" in st.session_state:
            progress = st.session_state.progress
            lesson_vocab = get_lesson_vocabulary(lesson_id)
            found_words = extract_vocabulary(response, lesson_vocab)

            # Record each vocab item
            for word in found_words:
                english = next(
                    (v["english"] for v in lesson_vocab if v["malay"] == word), ""
                )
                record_vocab(progress, word, english, lesson_id)

            # Record session data (count user messages in this lesson)
            lesson_msgs = len([
                m for m in st.session_state.messages if m["role"] == "user"
            ])
            record_session(progress, lesson_id, lesson_msgs, found_words)

            # Sync completed_lessons in session state
            st.session_state.completed_lessons = progress.get("completed_lessons", [])

            # Check if lesson is now complete
            if lesson_id not in st.session_state.completed_lessons:
                if check_lesson_completion(progress, lesson_id):
                    lesson = get_lesson(lesson_id)
                    complete_lesson(progress, lesson_id)
                    st.session_state.completed_lessons = progress["completed_lessons"]
                    st.session_state.active_lesson = progress["current_lesson"]
                    st.balloons()
                    st.toast(
                        f"Lesson {lesson_id} complete! You've mastered {lesson['title']}!",
                        icon="🎉",
                    )

        # Rerun to refresh recommended prompts based on updated conversation
        st.rerun()
