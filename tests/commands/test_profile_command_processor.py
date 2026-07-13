from unittest.mock import MagicMock

import pytest

from src.commands.profile_command_processor import ProfileCommandProcessor
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_sets_persona_and_resets_history() -> None:
    store = UserStateStoreMemory()
    store.set_topic(1, "existing topic")
    store.append_turn(1, "user", "hi")

    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy matey!"

    processor = ProfileCommandProcessor(store, factory_mock)

    result = processor.process(1, "a pirate")

    assert result == "Ahoy matey!"

    state = store.get(1)
    assert state.persona == "a pirate"
    assert state.topic == "existing topic"
    assert len(state.history) == 1
    assert state.history[0] == {"role": "assistant", "content": "Ahoy matey!"}


def test_process_applies_default_topic_if_unset() -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Hello."

    processor = ProfileCommandProcessor(store, factory_mock)
    processor.process(1, "a pirate")

    state = store.get(1)
    assert state.topic == "casual daily conversation"


def test_process_returns_fallback_and_logs_on_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = UserStateStoreMemory()
    store.set_topic(1, "existing topic")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = Exception("API error")

    processor = ProfileCommandProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = processor.process(1, "a pirate")

    assert result == "An error occurred. Try again in a moment.\n\nAPI error"
    assert (
        "Failed to generate profile command opening message for user_id=1"
        in caplog.text
    )
