import logging

from src.commands.command_processor import CommandProcessor
from src.error_messages import format_fallback_message
from src.messages.message_processor import LLMClientFactoryProtocol
from src.state.user_state_store import UserStateStore

DEFAULT_PERSONA = "a casual American person"
DEFAULT_TOPIC = "casual daily conversation"
HELP_MENTION = "You can use /help for details."
logger = logging.getLogger(__name__)


class StartCommandProcessor(CommandProcessor):
    def __init__(
        self,
        user_state_store: UserStateStore,
        llm_client_factory: LLMClientFactoryProtocol,
    ) -> None:
        super().__init__(user_state_store)
        self.llm_client = llm_client_factory.create()

    def process(self, user_id: int, args: str) -> str:
        self._apply_defaults(user_id)
        self.user_state_store.reset_history(user_id)
        state = self.user_state_store.get(user_id)

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are {state.persona}. We are talking about {state.topic}. "
                    "Start the conversation naturally and in character."
                ),
            }
        ]

        try:
            opening_msg = self.llm_client.send(messages)
            self.user_state_store.append_turn(user_id, "assistant", opening_msg)
            return f"{HELP_MENTION}\n\n{opening_msg}"
        except Exception as error:
            logger.exception(
                "Failed to generate start command opening message for user_id=%s",
                user_id,
            )
            return format_fallback_message(error)

    def _apply_defaults(self, user_id: int) -> None:
        state = self.user_state_store.get(user_id)
        if not state.persona:
            self.user_state_store.set_persona(user_id, DEFAULT_PERSONA)
        if not state.topic:
            self.user_state_store.set_topic(user_id, DEFAULT_TOPIC)
