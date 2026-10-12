import logging

from error_messages import format_fallback_message
from messages.conversation_style import BRIEF_CONVERSATION_STYLE
from messages.message_processor import MessageProcessor
from state.user_state_store import FeedbackMode, UserState

logger = logging.getLogger(__name__)


class TextMessageProcessor(MessageProcessor):
    async def process(self, user_id: int, content: str) -> dict[str, str | None]:
        state = self.user_state_store.get(user_id)

        try:
            persona_reply = await self._generate_persona_reply(state, content)
            correction = (
                None
                if state.feedback == "off"
                else await self._generate_correction(content, state.feedback)
            )
            self._update_history(user_id, content, persona_reply)
            return {
                "persona_reply": persona_reply,
                "correction": correction,
            }
        except Exception as error:
            logger.exception("Failed to process text message for user_id=%s", user_id)
            return {
                "persona_reply": format_fallback_message(error),
                "correction": None,
            }

    def _build_persona_prompt(self, state: UserState) -> list[dict[str, str]]:
        content = (
            f"You are {state.persona}. We are talking about {state.topic}. "
            "Respond naturally and stay in character. "
            f"{BRIEF_CONVERSATION_STYLE}"
        )
        messages = [{"role": "system", "content": content}]
        messages.extend(state.history)  # type: ignore[arg-type]
        return messages

    async def _generate_persona_reply(self, state: UserState, content: str) -> str:
        messages = self._build_persona_prompt(state)
        messages.append({"role": "user", "content": content})
        return await self.llm_client.send(messages)

    async def _generate_correction(
        self, content: str, feedback: FeedbackMode = "all"
    ) -> str | None:
        sys_msg = (
            "You are an English teacher. Review the user's message for grammar "
            "or unnatural phrasing. If it is perfect or mostly fine, respond "
            "EXACTLY with 'NO_CORRECTION'. If there are errors, provide the "
            "corrected sentence and a brief explanation."
        )
        if feedback == "important":
            sys_msg = (
                "You are an English teacher. Report only errors that materially "
                "affect grammar or meaning, such as incorrect tense, agreement, "
                "or wording that changes or obscures the intended meaning. "
                "Ignore minor stylistic improvements and acceptable informal phrasing. "
                "If there are no important errors, respond EXACTLY with "
                "'NO_CORRECTION'. Otherwise provide the corrected sentence and "
                "a brief explanation of only the important errors, in a plain "
                "teacher voice."
            )
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": content},
        ]
        correction = (await self.llm_client.send(messages)).strip()
        if correction == "NO_CORRECTION" or not correction:
            return None
        return correction

    def _update_history(
        self, user_id: int, user_content: str, bot_content: str
    ) -> None:
        self.user_state_store.append_turn(user_id, "user", user_content)
        self.user_state_store.append_turn(user_id, "assistant", bot_content)
