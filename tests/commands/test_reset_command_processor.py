from src.commands.reset_command_processor import RESET_MESSAGE, ResetCommandProcessor
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_only_resets_history() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")
    store.append_turn(1, "user", "hello")
    store.append_turn(1, "assistant", "ahoy")
    processor = ResetCommandProcessor(store)

    result = processor.process(1, "")

    assert result == RESET_MESSAGE
    state = store.get(1)
    assert state.persona == "pirate"
    assert state.topic == "ships"
    assert state.history == []
