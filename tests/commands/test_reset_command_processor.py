from unittest.mock import MagicMock

import pytest

from src.commands.reset_command_processor import ResetCommandProcessor
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_resets_history_and_returns_message() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")
    store.append_turn(1, "user", "hello")
    store.append_turn(1, "assistant", "ahoy")

    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.return_value = "Ahoy matey!"

    processor = ResetCommandProcessor(store, factory_mock)

    result = processor.process(1, "")

    assert result == "Ahoy matey!"

    state = store.get(1)
    # Persona and topic untouched
    assert state.persona == "pirate"
    assert state.topic == "ships"
    # History was reset and then the opening message appended
    assert len(state.history) == 1
    assert state.history[0] == {"role": "assistant", "content": "Ahoy matey!"}


def test_process_error(caplog: pytest.LogCaptureFixture) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = Exception("API error")

    processor = ResetCommandProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = processor.process(1, "")

    assert result == "An error occurred. Try again in a moment."
    assert (
        "Failed to generate reset command opening message for user_id=1" in caplog.text
    )
