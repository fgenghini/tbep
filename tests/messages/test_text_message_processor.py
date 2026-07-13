from unittest.mock import MagicMock

import pytest

from src.messages.text_message_processor import TextMessageProcessor
from src.state.user_state_store_memory import UserStateStoreMemory


def test_process_returns_both_reply_and_correction() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")

    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    # 1st call: persona reply. 2nd call: correction.
    llm_mock.send.side_effect = ["Ahoy!", "You should say 'hello' instead."]

    processor = TextMessageProcessor(store, factory_mock)

    result = processor.process(1, "hi")

    assert result["persona_reply"] == "Ahoy!"
    assert result["correction"] == "You should say 'hello' instead."

    state = store.get(1)
    assert len(state.history) == 2
    assert state.history[0] == {"role": "user", "content": "hi"}
    assert state.history[1] == {"role": "assistant", "content": "Ahoy!"}


def test_process_returns_none_correction() -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = ["Hello there.", "NO_CORRECTION"]

    processor = TextMessageProcessor(store, factory_mock)

    result = processor.process(1, "Hello")

    assert result["persona_reply"] == "Hello there."
    assert result["correction"] is None


def test_process_returns_fallback_on_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send.side_effect = Exception("API failed")

    processor = TextMessageProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = processor.process(1, "Hello")

    assert (
        result["persona_reply"] == "An error occurred. Try again in a moment.\n\nAPI failed"
    )
    assert result["correction"] is None
    assert "Failed to process text message for user_id=1" in caplog.text

    # History shouldn't be updated on error
    state = store.get(1)
    assert len(state.history) == 0
