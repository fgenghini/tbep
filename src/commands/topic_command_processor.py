from src.commands.command_processor import CommandProcessor

TOPIC_UPDATED_MESSAGE = "Topic updated. Use /start to start a new conversation."


class TopicCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        self.user_state_store.set_topic(user_id, args)
        return TOPIC_UPDATED_MESSAGE
