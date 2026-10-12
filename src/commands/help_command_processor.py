from commands.command_processor import CommandProcessor

HELP_TEXT = """Welcome to TBEP! Here are the available commands:
/start - Start a new conversation; defaults apply only to unset profile/topic
/profile <persona> - Set the persona for the next conversation
/topic <topic> - Set the topic for the next conversation
/style brief|balanced|detailed - Choose reply length (default: brief)
       Use /style without arguments to see your current choice
/reset - Clear history but keep preferences; use /start to start again
/feedback off|important|all - Corrections: off, important errors, or all (default)
/stats - Show persona, topic, style, feedback, and stored message count
/help - Show this help message

Whenever you type a message, I will reply in character and provide English
corrections according to your feedback setting, in a separate teacher voice.
Tap “Say it another way” on the latest reply for one alternative phrasing,
even with feedback off. Older buttons expire when you send a new sentence,
use /reset or /start, or Worker state resets.
Preferences can reset on Worker restart."""


class HelpCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        return HELP_TEXT
