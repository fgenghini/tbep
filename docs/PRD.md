# PRD: TBEP (Telegram Bot for English Practice)

## 1. Overview

**Product name:** TBEP (Telegram Bot for English Practice)

**Summary:** A Telegram bot that helps users practice English through natural, roleplay-style conversation. The bot assumes a configurable "persona" (e.g., teenager, businessperson, elderly Londoner) and converses naturally around a user-chosen topic, while separately providing direct grammar/fluency corrections after each user message. Initial release is text-only; voice chat is a planned future extension.

**Primary user goal:** Practice conversational English in a low-pressure, engaging way, with actionable feedback on mistakes.

**Core value proposition:** Unlike generic grammar checkers or static lesson bots, this bot keeps the user *in a conversation* — the roleplay stays immersive and in-character, while corrections are delivered as a separate, clear, no-nonsense layer.

---

## 2. Goals & Non-Goals

### Goals
- Let users configure a conversational persona in natural language.
- Let users set a topic, with the bot proactively opening the conversation.
- Maintain an in-character, natural-sounding conversation driven by an LLM.
- Provide grammar/naturalness corrections on the user's messages, delivered plainly regardless of persona tone.
- Support easy reset of the conversation via `/profile` and `/topic`.

### Non-Goals (for this release)
- Voice chat (explicitly deferred to a later phase).
- Multi-user group chat support (assume 1:1 DM with the bot).
- Formal curriculum, progress tracking, or gamification (may be considered later).
- Multi-language support (target language is English only).

---

## 3. Users & Use Case

**Target user:** Someone learning or practicing English who wants conversational practice that feels realistic, not like a textbook drill.

**Example flow:**
1. User opens chat with bot for the first time.
2. Bot greets and mentions that `/help` is available for more info on how it works.
3. User runs `/profile a grumpy old man from London who complains a lot`.
4. Bot confirms the persona is set.
5. User runs `/topic ordering food at a restaurant`.
6. Bot immediately opens the conversation in character, introducing the topic naturally (e.g., in-character small talk that leads into the topic — not a meta-announcement like "Let's talk about restaurants").
7. User replies; bot responds in character AND appends a separate, clearly-formatted correction of the user's last message (if there were errors — see Section 5.3).
8. Conversation continues turn by turn.
9. User can run `/profile` or `/topic` again at any time to reset and start fresh.

---

## 4. Key Concepts

- **Profile (Persona):** A free-text description of the character/personality the bot should roleplay as during conversation. Affects tone, vocabulary, slang usage, formality — but never affects the correction layer.
- **Topic:** A free-text description of the subject the conversation should center on. Setting a topic triggers the bot to immediately produce an in-character opening message that naturally leads into that subject.
- **Conversation turn:** One user message + one bot response. Each bot response has two parts: (a) the in-character reply, (b) the correction/feedback on the user's prior message.
- **Reset:** Both `/profile` and `/topic` clear prior conversation history/context and start a new session state.

---

## 5. Functional Requirements

### 5.1 Commands

| Command | Behavior |
|---|---|
| `/start` | Onboards new users with a short greeting that mentions the `/help` command for details on how the bot works. Applies the default persona ("casual American person") and default topic ("casual daily conversation"), and immediately starts the conversation with an in-character opening message, so the bot is usable without any configuration. |
| `/profile <description>` | Sets or replaces the persona. Resets the conversation (clears message history/context). Immediately starts a new conversation in character using the current topic (default topic if none was explicitly set). |
| `/topic <description>` | Sets or replaces the topic. Resets the conversation. Bot immediately sends an in-character opening message that naturally introduces/leads into the topic — no separate "confirmation" message before it; the opening message *is* the confirmation, delivered in persona. Uses the current persona (default persona if none was explicitly set). |
| `/help` | Explains available commands and how corrections work. |
| `/reset` | Explicit reset without changing profile/topic — clears conversation history and immediately starts a new in-character opening message. |

**Defaults:** A brand-new user (or one who hasn't customized yet) gets persona = "a casual American person" and topic = "casual daily conversation." Both `/profile` and `/topic` — as well as `/start` — immediately trigger an in-character opening message using whatever persona/topic is currently active (custom or default).

### 5.2 Conversation Behavior (In-Character Layer)
- The bot must respond as naturally and human-like as possible, consistent with the configured persona (tone, vocabulary, slang, formality, typical phrasing).
- The bot should maintain conversation continuity/context within a session (i.e., remember what's been said since the last reset).
- The bot should avoid breaking character within the in-character portion of its reply (e.g., no meta-commentary like "As an AI...").
- When `/topic` is set, the very next bot message (with no user input required) must open the conversation in character, naturally incorporating the topic.

### 5.3 Correction Layer
- After each user message, the bot evaluates it for grammar errors, awkward phrasing, or unnatural word choice.
- If issues are found: the bot includes a corrections section separate from the in-character reply — direct, clear, plain tone (not in persona voice), regardless of what persona is active.
- If no issues are found: no correction message is shown at all — only the in-character reply is sent.
- Correction should show something like: the corrected version of the sentence, and briefly, what was wrong / how to make it sound more natural.
- **Visual separation:** the in-character reply and the correction are sent as two separate Telegram messages — one persona message, one correction message — so users can clearly distinguish "the conversation" from "the feedback."

### 5.4 LLM Integration
- An LLM drives both the in-character conversation generation and the correction/feedback generation.
- These can be two distinct LLM calls/prompts per turn (one for persona reply, one for correction), or a single call producing structured output split into two parts — implementation detail, not prescribed here given product-level scope.
- The system should be designed provider-agnostically (no hard dependency on a specific LLM vendor), so the underlying model can be swapped.

### 5.5 State & Reset Behavior
- Each user has their own independent bot state (persona, topic, conversation history).
- Running `/profile` or `/topic` clears the existing conversation history so the LLM doesn't carry over context from a prior, now-irrelevant scenario.
- Persona and topic settings themselves persist independently of each other unless explicitly overwritten (e.g., changing topic does not require re-entering the profile — the last-set profile is reused with the new topic, and vice versa).
- **Conversation history for v1:** the full session history (since the last reset) is sent to the LLM as context — no truncation or capping in this release. Capping/summarization may be introduced later if context size or cost becomes a concern.

---

## 6. Non-Functional Requirements

- **Latency:** Bot responses (both persona reply and correction) should arrive within a few seconds to preserve a natural chat feel.
- **Reliability:** Should gracefully handle LLM API errors/timeouts without leaving the user with no response. On failure, the bot replies with a plain fallback message: "An error occurred. Try again in a moment."
- **Privacy:** Conversations may include personal practice content; store only what's needed for session context, and be clear about what is retained.
- **Extensibility:** Architecture should not preclude adding voice chat later (e.g., text generation layer should be separable from the eventual voice input/output layer).
- **Language stack:** Backend implemented in Python.

---

## 7. Future Considerations (Out of Scope for v1)

- Voice chat support (speech-to-text input, text-to-speech output in persona voice).
- Progress tracking / recurring error pattern summaries over time.
- Difficulty levels (e.g., simplify persona vocabulary for beginners).
- Preset persona/topic library for users who don't want to write free text.
- Multi-turn topic suggestions ("what should we talk about next?").
- Group chat / multiple simultaneous learners.

---

## 8. Decisions Log

| Question | Decision |
|---|---|
| Default persona/topic for new/unconfigured users? | Yes — default persona: "a casual American person"; default topic: "casual daily conversation." Conversation starts immediately using these defaults. |
| Show a "looks good!" note when there are no errors? | No — say nothing; only the in-character reply is sent when no corrections are needed. |
| Cap conversation history sent to the LLM? | No, not for v1 — use full session history since last reset. Revisit if cost/context size becomes an issue. |
| Should `/profile` alone also auto-start the conversation? | Yes — both `/profile` and `/topic` immediately trigger an in-character opening message. |
| Moderation/guardrails on user-defined personas? | No — left unrestricted for this release. |
| Include `/help` and `/reset` commands in v1? | Yes — both are part of the required command set. |
| Correction format — separate message or combined with persona reply? | Separate Telegram messages — persona reply and correction are sent independently. |
| Fallback message on LLM error/timeout? | Fixed text: "An error occurred. Try again in a moment." |
| Should onboarding explain full bot usage inline? | No — greeting just mentions that `/help` is available for details. |

