import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from messages.text_message_processor import TextMessageProcessor
from state.user_state_store_memory import UserStateStoreMemory


@pytest.mark.parametrize(
    ("persona", "topic"),
    [
        ("a casual American person", "casual daily conversation"),
        ("a pirate", "sailing"),
    ],
)
def test_reply_prompt_includes_brief_style_without_affecting_corrections(
    persona: str, topic: str
) -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, persona)
    store.set_topic(1, topic)
    store.append_turn(1, "assistant", "Hello!")
    llm = MagicMock()
    llm.send = AsyncMock(side_effect=["Sounds fun!", "NO_CORRECTION"])
    factory = MagicMock()
    factory.create.return_value = llm

    result = asyncio.run(TextMessageProcessor(store, factory).process(1, "I like it."))

    reply_messages, correction_messages = [
        call.args[0] for call in llm.send.call_args_list
    ]
    assert reply_messages == [
        {
            "role": "system",
            "content": (
                f"You are {persona}. We are talking about {topic}. "
                "Respond naturally and stay in character. "
                "Keep replies conversational and brief by default: one or two short "
                "sentences. Respond directly to the learner and ask at most one "
                "relevant follow-up question. Avoid lists, lectures, and unnecessary "
                "repetition. "
                "Give more detail when the learner asks for it."
            ),
        },
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "I like it."},
    ]
    assert correction_messages == [
        {
            "role": "system",
            "content": (
                "You are an English teacher. Review the user's message for grammar "
                "or unnatural phrasing. If it is perfect or mostly fine, respond "
                "EXACTLY with 'NO_CORRECTION'. If there are errors, provide the "
                "corrected sentence and a brief explanation."
            ),
        },
        {"role": "user", "content": "I like it."},
    ]
    assert result["persona_reply"] == "Sounds fun!"
    assert result["correction"] is None
    assert store.get(1).history == [
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "I like it."},
        {"role": "assistant", "content": "Sounds fun!"},
    ]


def test_process_returns_both_reply_and_correction() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")

    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    # 1st call: persona reply. 2nd call: correction.
    llm_mock.send = AsyncMock(side_effect=["Ahoy!", "You should say 'hello' instead."])

    processor = TextMessageProcessor(store, factory_mock)

    result = asyncio.run(processor.process(1, "hi"))

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
    llm_mock.send = AsyncMock(side_effect=["Hello there.", "NO_CORRECTION"])

    processor = TextMessageProcessor(store, factory_mock)

    result = asyncio.run(processor.process(1, "Hello"))

    assert result["persona_reply"] == "Hello there."
    assert result["correction"] is None


def test_process_returns_fallback_on_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    store = UserStateStoreMemory()
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock
    llm_mock.send = AsyncMock(side_effect=Exception("API failed"))

    processor = TextMessageProcessor(store, factory_mock)

    with caplog.at_level("ERROR"):
        result = asyncio.run(processor.process(1, "Hello"))

    assert (
        result["persona_reply"]
        == "An error occurred. Try again in a moment.\n\nAPI failed"
    )
    assert result["correction"] is None
    assert "Failed to process text message for user_id=1" in caplog.text

    # History shouldn't be updated on error
    state = store.get(1)
    assert len(state.history) == 0
