from src.commands.command_processor import CommandProcessor

RESET_MESSAGE = "Conversation history cleared. Use /start to start a new conversation."


class ResetCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        self.user_state_store.reset_history(user_id)
        return RESET_MESSAGE
