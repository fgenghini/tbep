from src.commands.command_processor import CommandProcessor

PROFILE_UPDATED_MESSAGE = "Profile updated. Use /start to start a new conversation."


class ProfileCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        self.user_state_store.set_persona(user_id, args)
        return PROFILE_UPDATED_MESSAGE
