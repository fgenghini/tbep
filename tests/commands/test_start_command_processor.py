from unittest.mock import AsyncMock, MagicMock

import pytest

from commands.start_command_processor import (
    DEFAULT_PERSONA,
    DEFAULT_TOPIC,
    StartCommandProcessor,
)
from state.user_state_store_memory import UserStateStoreMemory


@pytest.mark.parametrize(
    ("persona", "topic"),
    [(DEFAULT_PERSONA, DEFAULT_TOPIC), ("a pirate", "sailing")],
)
def test_opening_prompt_includes_brief_style_with_persona_and_topic(
    run_async, persona: str, topic: str
) -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, persona)
    store.set_topic(1, topic)
    llm = MagicMock()
    llm.send = AsyncMock(return_value="Hello!")
    factory = MagicMock()
    factory.create.return_value = llm

    run_async(StartCommandProcessor(store, factory).process(1, ""))

    messages = llm.send.call_args.args[0]
    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == (
        f"You are {persona}. We are talking about {topic}. "
        "Start the conversation naturally and in character. "
        "Keep replies conversational and brief by default: one or two short "
        "sentences. Respond directly to the learner and ask at most one relevant "
        "follow-up question. Avoid lists, lectures, and unnecessary repetition. "
        "Give more detail when the learner asks for it."
    )


def test_process_applies_defaults_for_brand_new_user(run_async) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send = AsyncMock(return_value="How's your day going?")

    processor = StartCommandProcessor(store, factory_mock)

    run_async(processor.process(1, ""))

    state = store.get(1)
    assert state.persona == DEFAULT_PERSONA
    assert state.topic == DEFAULT_TOPIC


def test_process_does_not_override_existing_persona_or_topic(run_async) -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "a pirate")
    store.set_topic(1, "sailing")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send = AsyncMock(return_value="Ahoy!")

    processor = StartCommandProcessor(store, factory_mock)

    run_async(processor.process(1, ""))

    state = store.get(1)
    assert state.persona == "a pirate"
    assert state.topic == "sailing"


def test_process_resets_history_and_returns_opening_message_with_help(
    run_async,
) -> None:
    store = UserStateStoreMemory()
    store.append_turn(1, "user", "old message")
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send = AsyncMock(return_value="How's your day going?")

    processor = StartCommandProcessor(store, factory_mock)

    result = run_async(processor.process(1, ""))

    assert "/help" in result
    assert "How's your day going?" in result
    assert store.get(1).history == [
        {"role": "assistant", "content": "How's your day going?"}
    ]


def test_process_returns_fallback_and_logs_on_error(
    caplog: pytest.LogCaptureFixture,
    run_async,
) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send = AsyncMock(side_effect=Exception("API error"))

    processor = StartCommandProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = run_async(processor.process(1, ""))

    assert result == "An error occurred. Try again in a moment.\n\nAPI error"
    assert (
        "Failed to generate start command opening message for user_id=1" in caplog.text
    )
