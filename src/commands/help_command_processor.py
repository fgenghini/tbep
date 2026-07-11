from src.commands.command_processor import CommandProcessor

HELP_TEXT = """Welcome to TBEP! Here are the available commands:
/start - Start a new conversation with default settings
/profile <persona> - Set a new persona and restart the conversation
/topic <topic> - Set a new topic and restart the conversation
/reset - Clear the conversation history but keep the persona and topic
/help - Show this help message

Whenever you type a message, I will reply in character and provide English
corrections if needed!"""


class HelpCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        return HELP_TEXT
