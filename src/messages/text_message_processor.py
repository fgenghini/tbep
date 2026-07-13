import logging

from src.error_messages import format_fallback_message
from src.messages.message_processor import MessageProcessor
from src.state.user_state_store import UserState

logger = logging.getLogger(__name__)


class TextMessageProcessor(MessageProcessor):
    def process(self, user_id: int, content: str) -> dict[str, str | None]:
        state = self.user_state_store.get(user_id)

        try:
            persona_reply = self._generate_persona_reply(state, content)
            correction = self._generate_correction(content)
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
            "Respond naturally and stay in character."
        )
        messages = [{"role": "system", "content": content}]
        messages.extend(state.history)  # type: ignore[arg-type]
        return messages

    def _generate_persona_reply(self, state: UserState, content: str) -> str:
        messages = self._build_persona_prompt(state)
        messages.append({"role": "user", "content": content})
        return self.llm_client.send(messages)

    def _generate_correction(self, content: str) -> str | None:
        sys_msg = (
            "You are an English teacher. Review the user's message for grammar "
            "or unnatural phrasing. If it is perfect or mostly fine, respond "
            "EXACTLY with 'NO_CORRECTION'. If there are errors, provide the "
            "corrected sentence and a brief explanation."
        )
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": content},
        ]
        correction = self.llm_client.send(messages).strip()
        if correction == "NO_CORRECTION" or not correction:
            return None
        return correction

    def _update_history(
        self, user_id: int, user_content: str, bot_content: str
    ) -> None:
        self.user_state_store.append_turn(user_id, "user", user_content)
        self.user_state_store.append_turn(user_id, "assistant", bot_content)
