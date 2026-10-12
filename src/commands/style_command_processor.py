from typing import get_args

from commands.command_processor import CommandProcessor
from state.user_state_store import ReplyStyle


class StyleCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        choice = args.strip().lower()
        for style in get_args(ReplyStyle):
            if choice == style:
                self.user_state_store.set_style(user_id, style)
                return f"Style updated to {style}. Applies to your next reply."
        current = self.user_state_store.get(user_id).style
        return f"Current style: {current}. Use /style brief|balanced|detailed."
