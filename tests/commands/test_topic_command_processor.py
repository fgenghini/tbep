from unittest.mock import MagicMock

import pytest

from src.commands.topic_command_processor import TopicCommandProcessor
from src.state.user_state_store import UserState
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_sets_topic_on_user_state_store() -> None:
    store_mock = MagicMock()
    store_mock.get.return_value = UserState(persona="existing persona", topic="ships")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy matey!"

    processor = TopicCommandProcessor(store_mock, factory_mock)

    processor.process(1, "ships")

    store_mock.set_topic.assert_called_once_with(1, "ships")


def test_process_resets_history() -> None:
    store_mock = MagicMock()
    store_mock.get.return_value = UserState(persona="existing persona", topic="ships")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy matey!"

    processor = TopicCommandProcessor(store_mock, factory_mock)

    processor.process(1, "ships")

    store_mock.reset_history.assert_called_once_with(1)


def test_process_sets_topic_and_resets_history() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "existing persona")
    store.append_turn(1, "user", "hi")

    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy matey!"

    processor = TopicCommandProcessor(store, factory_mock)

    result = processor.process(1, "ships")

    assert result == "Ahoy matey!"

    state = store.get(1)
    assert state.topic == "ships"
    assert state.persona == "existing persona"
    assert len(state.history) == 1
    assert state.history[0] == {"role": "assistant", "content": "Ahoy matey!"}


def test_process_applies_default_persona_if_unset() -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Hello."

    processor = TopicCommandProcessor(store, factory_mock)
    processor.process(1, "ships")

    state = store.get(1)
    assert state.persona == "a casual American person"


def test_process_returns_opening_message_from_llm() -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "So, what's your favorite ship?"

    processor = TopicCommandProcessor(store, factory_mock)

    result = processor.process(1, "ships")

    assert result == "So, what's your favorite ship?"
    llm_mock.send.assert_called_once()


def test_process_returns_fallback_and_logs_on_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = Exception("API error")

    processor = TopicCommandProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = processor.process(1, "ships")

    assert result == "An error occurred. Try again in a moment.\n\nAPI error"
    assert (
        "Failed to generate topic command opening message for user_id=1" in caplog.text
    )
