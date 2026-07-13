from unittest.mock import MagicMock

from src.commands.topic_command_processor import (
    TOPIC_UPDATED_MESSAGE,
    TopicCommandProcessor,
)
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_only_sets_topic() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "existing persona")
    store.append_turn(1, "user", "hi")
    store.append_turn(1, "assistant", "hello")
    processor = TopicCommandProcessor(store)

    result = processor.process(1, "ships")

    assert result == TOPIC_UPDATED_MESSAGE
    state = store.get(1)
    assert state.topic == "ships"
    assert state.persona == "existing persona"
    assert state.history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_process_does_not_apply_defaults_or_change_conversation_state() -> None:
    store_mock = MagicMock()
    processor = TopicCommandProcessor(store_mock)

    processor.process(1, "ships")

    store_mock.set_topic.assert_called_once_with(1, "ships")
    store_mock.set_persona.assert_not_called()
    store_mock.reset_history.assert_not_called()
    store_mock.append_turn.assert_not_called()
