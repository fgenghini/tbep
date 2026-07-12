from unittest.mock import MagicMock

import pytest

from src.commands.start_command_processor import (
    DEFAULT_PERSONA,
    DEFAULT_TOPIC,
    StartCommandProcessor,
)
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_applies_defaults_for_brand_new_user() -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "How's your day going?"

    processor = StartCommandProcessor(store, factory_mock)

    processor.process(1, "")

    state = store.get(1)
    assert state.persona == DEFAULT_PERSONA
    assert state.topic == DEFAULT_TOPIC


def test_process_does_not_override_existing_persona_or_topic() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "a pirate")
    store.set_topic(1, "sailing")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy!"

    processor = StartCommandProcessor(store, factory_mock)

    processor.process(1, "")

    state = store.get(1)
    assert state.persona == "a pirate"
    assert state.topic == "sailing"


def test_process_resets_history_and_returns_opening_message_with_help() -> None:
    store = UserStateStoreMemory()
    store.append_turn(1, "user", "old message")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "How's your day going?"

    processor = StartCommandProcessor(store, factory_mock)

    result = processor.process(1, "")

    assert "/help" in result
    assert "How's your day going?" in result
    assert store.get(1).history == [
        {"role": "assistant", "content": "How's your day going?"}
    ]


def test_process_returns_fallback_and_logs_on_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = Exception("API error")

    processor = StartCommandProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = processor.process(1, "")

    assert result == "An error occurred. Try again in a moment."
    assert (
        "Failed to generate start command opening message for user_id=1" in caplog.text
    )
