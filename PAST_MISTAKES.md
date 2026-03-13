# MalayChat — Past Mistakes & Lessons Learned

## 1. Repetition detector false positives on breakdown format

**What happened:** After adding word-by-word breakdowns to the system prompt, the repetition detector started killing responses after only 67 tokens. The model would output one phrase and get cut off mid-response.

**Root cause:** The breakdown format naturally repeats short patterns like `*word* (meaning) + ` across multiple words. The old thresholds (`min_length=80`, phrase check starting at length 15) were too aggressive and flagged these as repetition loops.

**Fix:** Relaxed thresholds — `min_length` 80 → 250, `window` 60 → 80, minimum phrase length 15 → 30.

**Lesson:** When changing the output format, check if safety mechanisms (like repetition detection) are calibrated for the new format.

---

## 2. System prompt too complex for 8B model

**What happened:** The system prompt used nested bullet points to distinguish between translation requests and conversation/role-play requests. The model ignored the conditional logic entirely and just translated everything — including requests like "Can we have a conversation at a market?" which should trigger role-play.

**Root cause:** Molmo2-8B (8B parameters) doesn't reliably follow multi-level conditional instructions. Nested structures like "If X, then: - sub-rule 1 - sub-rule 2" were lost.

**Fix:** Rewrote prompts with flat structure, short paragraphs, explicit "IMPORTANT: Do NOT..." instructions at the top, and a concrete example of correct output. The model followed these much more reliably.

**Lesson:** For small models, keep prompts flat and explicit. Lead with prohibitions. Show don't tell — include a concrete example of the exact output format expected.

---

## 3. Model wouldn't stay in character during role-play

**What happened:** Even after simplifying the system prompt with role-play instructions, the model would break character. When the user said "aku nak beli ikan" (I want to buy fish) during a market role-play, the model translated the user's message instead of responding as the seller.

**Root cause:** The 8B model couldn't reliably infer role-play intent from conversational context alone. A single line in the system prompt saying "if the user wants to role-play, play along" wasn't strong enough.

**Fix:** Added an explicit role-play toggle (`st.toggle`) that injects a dedicated `ROLEPLAY_CONTEXT` block into the system prompt with forceful stay-in-character instructions: "ROLEPLAY MODE IS ON. You MUST stay in character. Do NOT translate the user's messages."

**Lesson:** When a small model can't reliably detect intent, give the user an explicit control to signal it. A UI toggle that changes the system prompt is more reliable than hoping the model figures it out from context.

---

## 4. LLM just echoing raw translations without teaching

**What happened:** When tool results (translations) were injected into the system prompt, the model would just parrot them back — e.g., responding with only "terima kasih" instead of providing an example sentence with breakdown.

**Root cause:** The system prompt said "Use the provided tool results for Malay translations" which the model interpreted as "just output the tool result."

**Fix:** Changed wording to "If tool results are provided, use them as the correct Malay translation" (reference, not the answer) and added "Always include the breakdown. Never just give the translation alone."

**Lesson:** Be precise about the role of injected context. "Use X" is ambiguous — it can mean "output X" or "reference X." Spell out exactly what the model should do with it.

---

## 5. `st.chat_input` disappearing when handling suggestion button clicks

**What happened:** When a user clicked a recommended prompt button, the chat input box would vanish on the next render because `st.chat_input()` was inside an `else` branch that got skipped when processing the pending prompt.

**Root cause:** Streamlit requires `st.chat_input()` to be called on every render for the input box to appear. Putting it inside an `if/else` meant it wasn't rendered on button-click reruns.

**Fix:** Always call `st.chat_input()` unconditionally, then check for pending prompts separately:
```python
chat_input = st.chat_input("Type your message...")
if "pending_prompt" in st.session_state:
    user_input = st.session_state.pending_prompt
elif chat_input:
    user_input = chat_input
```

**Lesson:** Streamlit UI elements must be rendered every rerun to stay visible. Never conditionally skip rendering a persistent UI element.

---

## 6. Roleplay prompt appended instead of replaced — model still translates user's messages

**What happened:** With role-play toggle on, the model would still break down/explain the user's Malay input (e.g., when the user said "khabar baik", the model explained it instead of responding in character).

**Root cause:** The `ROLEPLAY_CONTEXT` was **appended** to the base `LEARNING_SYSTEM_PROMPT`. The base prompt contained "ALWAYS follow this format for every Malay sentence" which the 8B model treated as higher priority than the later "Do NOT translate the user's messages." Small models follow earlier/stronger instructions and struggle with contradictions.

**Fix:** Changed role-play from append to **replace** — `ROLEPLAY_SYSTEM_PROMPT` is a standalone prompt that completely replaces the base prompt when roleplay is active. It explicitly says "Only break down YOUR OWN replies, never the user's messages." No conflicting instructions.

**Lesson:** For small models, never append contradictory instructions to an existing prompt. If two modes have conflicting rules (e.g., "break down everything" vs "don't break down user messages"), use entirely separate prompts. The model can't reliably resolve contradictions.

---

## 7. Recommended prompts not refreshing after sending a message

**What happened:** After the user sent a message and received a response, the recommended prompt buttons still showed the old suggestions. They only updated when the user interacted with the app again (e.g., typed another message).

**Root cause:** Suggestions are computed during the render pass, before user input is processed. After the response streams and messages are appended to history, the page doesn't automatically re-render — Streamlit only reruns on widget interaction. So the suggestions shown are based on the pre-message conversation state.

**Fix:** Added `st.rerun()` at the end of every message exchange (after appending the response to history). This forces a re-render where `get_recommended_prompts()` sees the updated messages and generates fresh suggestions.

**Lesson:** In Streamlit, if you mutate session state during a render pass and need the UI to reflect the change, you must call `st.rerun()`. The page won't update on its own after processing — it waits for the next user interaction.

---

## 8. `check_lesson_completion` referencing undefined variable after refactor

**What happened:** After extracting `get_lesson_progress()` as a helper function, `check_lesson_completion()` still had the old code that referenced a `criteria` variable that no longer existed. This caused a `NameError` in production.

**Root cause:** During the refactor, the function was updated to call `get_lesson_progress()` at the top, but the old body (which computed `all_vocab`, `total_messages`, and compared against `criteria`) was left in place. The `criteria` variable was no longer defined since the `lesson = get_lesson(...)` and `criteria = lesson["completion_criteria"]` lines had been removed.

**Fix:** Replaced the entire body with a simple delegation to `get_lesson_progress()`:
```python
def check_lesson_completion(progress, lesson_id):
    lp = get_lesson_progress(progress, lesson_id)
    if lp["vocab_required"] == 0:
        return False
    return (lp["vocab_practiced"] >= lp["vocab_required"]
            and lp["messages"] >= lp["messages_required"])
```

**Lesson:** When extracting a helper function, delete the old code in the caller completely. Don't leave the old body alongside the new delegation — it's easy to miss stale variable references that only fail at runtime.

---

## 9. Streamlit Cloud ephemeral filesystem — JSON files disappear

**What happened:** Progress was originally designed to persist as a local JSON file (`~/.malaychat/progress.json`). This worked locally but all files were lost whenever Streamlit Cloud restarted or redeployed the app.

**Root cause:** Streamlit Cloud uses ephemeral containers. The filesystem is wiped on every restart/redeploy. There is no persistent local storage.

**Fix:** Switched to Google Sheets via `gspread` as the persistence layer. Considered three alternatives:
1. **Browser localStorage** (via `streamlit-local-storage`) — simplest, no external service, but tied to one browser/device
2. **Supabase free tier** — proper database, multi-device, but adds complexity and external dependency
3. **Google Sheets** — free, inspectable, multi-user, survives restarts, reasonable for the data volume

Chose Google Sheets because it's free, the data is small (key-value pairs), and it can be manually inspected/edited.

**Lesson:** When deploying to Streamlit Cloud, never rely on the local filesystem for persistence. Plan for an external store from the start. For small-scale apps, Google Sheets is a pragmatic middle ground between "no persistence" and "set up a real database."
