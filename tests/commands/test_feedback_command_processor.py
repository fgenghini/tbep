import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from commands.reset_command_processor import ResetCommandProcessor
from commands.start_command_processor import StartCommandProcessor
from commands.stats_command_processor import StatsCommandProcessor
from config import AppConfig
from main import Default, build_bot_components
from messages.text_message_processor import TextMessageProcessor


def components():
    return build_bot_components(
        AppConfig(
            telegram_bot_token="token",
            webhook_secret_path="secret",
            openai_api_key="key",
        )
    )


@pytest.mark.parametrize("choice", ["off", "important", "all", " IMPORTANT "])
def test_feedback_command_changes_only_feedback(choice: str) -> None:
    bot = components()
    store = bot.text.user_state_store
    store.set_style(1, "detailed")
    store.set_persona(1, "a pirate")
    store.set_topic(1, "ships")
    store.append_turn(1, "user", "Hello")
    result = bot.commands["feedback"].process(1, choice)
    state = store.get(1)
    assert state.feedback == choice.strip().lower()
    assert choice.strip().lower() in result
    assert state.style == "detailed"
    assert state.persona == "a pirate"
    assert state.topic == "ships"
    assert state.history == [{"role": "user", "content": "Hello"}]
    assert store.get(2).feedback == "all"
    assert f"Feedback: {state.feedback}" in StatsCommandProcessor(store).process(1, "")


@pytest.mark.parametrize("args", ["", "sometimes", "off all"])
def test_feedback_command_invalid_args_show_current_mode(args: str) -> None:
    bot = components()
    command = bot.commands["feedback"]
    command.process(1, "important")
    result = command.process(1, args)
    assert "important" in result
    assert "/feedback off|important|all" in result
    assert bot.text.user_state_store.get(1).feedback == "important"


@pytest.mark.parametrize("mode", ["off", "important", "all"])
def test_feedback_mode_keeps_persona_prompt_and_history(mode: str) -> None:
    bot = components()
    store = bot.text.user_state_store
    store.set_style(1, "detailed")
    store.set_persona(1, "a pirate")
    store.set_topic(1, "ships")
    store.append_turn(1, "assistant", "Ahoy!")
    bot.commands["feedback"].process(1, mode)
    llm = MagicMock()
    llm.send = AsyncMock(side_effect=["Welcome aboard!", "NO_CORRECTION"])
    factory = MagicMock()
    factory.create.return_value = llm
    result = asyncio.run(TextMessageProcessor(store, factory).process(1, "Hello"))
    assert result["persona_reply"] == "Welcome aboard!"
    assert result["correction"] is None
    assert llm.send.await_count == (1 if mode == "off" else 2)
    persona_prompt = llm.send.call_args_list[0].args[0][0]["content"]
    assert "You are a pirate. We are talking about ships." in persona_prompt
    assert "feedback" not in persona_prompt.lower()
    assert store.get(1).history == [
        {"role": "assistant", "content": "Ahoy!"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Welcome aboard!"},
    ]


@pytest.mark.parametrize(
    "answer, expected",
    [
        ("NO_CORRECTION", None),
        (" \nNO_CORRECTION ", None),
        ("", None),
        (
            "I went yesterday. Use the past tense.",
            "I went yesterday. Use the past tense.",
        ),
    ],
)
def test_important_feedback_uses_selective_teacher_prompt(answer, expected) -> None:
    bot = components()
    bot.commands["feedback"].process(1, "important")
    bot.text.llm_client = MagicMock()
    bot.text.llm_client.send = AsyncMock(side_effect=["Tell me more.", answer])
    result = asyncio.run(bot.text.process(1, "I go yesterday."))
    assert result["correction"] == expected
    messages = bot.text.llm_client.send.call_args_list[1].args[0]
    prompt = messages[0]["content"]
    assert "materially affect grammar or meaning" in prompt
    assert "minor stylistic" in prompt
    assert "NO_CORRECTION" in prompt
    assert messages[1] == {"role": "user", "content": "I go yesterday."}
    assert bot.text.user_state_store.get(1).history[-1]["content"] == "Tell me more."


def test_feedback_survives_reset_and_start() -> None:
    bot = components()
    store = bot.text.user_state_store
    bot.commands["feedback"].process(1, "off")
    ResetCommandProcessor(store).process(1, "")
    assert store.get(1).feedback == "off"
    llm = MagicMock()
    llm.send = AsyncMock(return_value="Hello!")
    factory = MagicMock()
    factory.create.return_value = llm
    asyncio.run(StartCommandProcessor(store, factory).process(1, ""))
    assert store.get(1).feedback == "off"
    assert llm.send.await_count == 1


def test_worker_routes_feedback_without_llm() -> None:
    instance = Default()
    instance.components = components()
    instance.components.text.llm_client = MagicMock()
    instance.components.text.llm_client.send = AsyncMock()
    replies = asyncio.run(
        instance._dispatch(
            {
                "message": {
                    "from": {"id": 1},
                    "chat": {"id": 1},
                    "text": "/feedback@tbep off",
                }
            }
        )
    )
    assert len(replies) == 1
    assert "off" in replies[0].text
    assert instance.components.text.user_state_store.get(1).feedback == "off"
    instance.components.text.llm_client.send.assert_not_awaited()
    assert "/feedback off|important|all" in instance.components.commands[
        "help"
    ].process(1, "")
