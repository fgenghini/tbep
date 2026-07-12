from src.commands.command_processor import CommandProcessor


class StatsCommandProcessor(CommandProcessor):
    def process(self, user_id: int, args: str) -> str:
        state = self.user_state_store.get(user_id)
        return (
            f"Persona: {state.persona}\n"
            f"Topic: {state.topic}\n"
            f"Messages stored: {len(state.history)}"
        )
