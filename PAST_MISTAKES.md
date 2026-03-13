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
