from commands.command_processor import CommandProcessor

HELP_TEXT = """Welcome to TBEP! Here are the available commands:
/start - Start a new conversation; defaults apply only to unset profile/topic
/profile <persona> - Set the persona for the next conversation
/topic <topic> - Set the topic for the next conversation
/style brief|balanced|detailed - Choose reply length (default: brief)
       Use /style without arguments to see your current choice
/reset - Clear history but keep the persona, topic, and style; use /start to start again
/stats - Show the current persona, topic, style, and stored message count
/help - Show this help message

Whenever you type a message, I will reply in character and provide English
corrections if needed!"""


class HelpCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        return HELP_TEXT
