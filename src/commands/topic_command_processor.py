from typing import Any

from src.commands.command_processor import CommandProcessor
from src.messages.message_processor import LLMClientFactoryProtocol
from src.state.user_state_store import UserStateStore


class TopicCommandProcessor(CommandProcessor):
    def __init__(
        self,
        user_state_store: UserStateStore,
        llm_client_factory: LLMClientFactoryProtocol,
        **llm_config: Any,
    ) -> None:
        super().__init__(user_state_store)
        self.llm_client = llm_client_factory.create(**llm_config)

    def process(self, user_id: int, args: str) -> str:
        self.user_state_store.set_topic(user_id, args)

        state = self.user_state_store.get(user_id)
        if not state.persona:
            self.user_state_store.set_persona(user_id, "a casual American person")
            state = self.user_state_store.get(user_id)

        self.user_state_store.reset_history(user_id)

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
            return opening_msg
        except Exception:
            return "An error occurred. Try again in a moment."
