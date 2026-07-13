from unittest.mock import MagicMock

from src.commands.profile_command_processor import (
    PROFILE_UPDATED_MESSAGE,
    ProfileCommandProcessor,
)
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_only_sets_persona() -> None:
    store = UserStateStoreMemory()
    store.set_topic(1, "existing topic")
    store.append_turn(1, "user", "hi")
    store.append_turn(1, "assistant", "hello")
    processor = ProfileCommandProcessor(store)

    result = processor.process(1, "a pirate")

    assert result == PROFILE_UPDATED_MESSAGE
    state = store.get(1)
    assert state.persona == "a pirate"
    assert state.topic == "existing topic"
    assert state.history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_process_does_not_apply_defaults_or_change_conversation_state() -> None:
    store_mock = MagicMock()
    processor = ProfileCommandProcessor(store_mock)

    processor.process(1, "a pirate")

    store_mock.set_persona.assert_called_once_with(1, "a pirate")
    store_mock.set_topic.assert_not_called()
    store_mock.reset_history.assert_not_called()
    store_mock.append_turn.assert_not_called()
