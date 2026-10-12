from typing import get_args

from commands.command_processor import CommandProcessor
from state.user_state_store import FeedbackMode


class FeedbackCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        choice = args.strip().lower()
        for mode in get_args(FeedbackMode):
            if choice == mode:
                self.user_state_store.set_feedback(user_id, mode)
                return f"Feedback updated to {mode}. Applies to your next message."
        current = self.user_state_store.get(user_id).feedback
        return f"Current feedback: {current}. Use /feedback off|important|all."
