from unittest.mock import AsyncMock, MagicMock

import pytest

from commands.reset_command_processor import ResetCommandProcessor
from commands.start_command_processor import StartCommandProcessor
from commands.stats_command_processor import StatsCommandProcessor
from commands.style_command_processor import StyleCommandProcessor
from config import AppConfig
from main import build_bot_components
from messages.text_message_processor import TextMessageProcessor
from state.user_state_store_memory import UserStateStoreMemory


def test_style_is_registered_and_defaults_to_brief() -> None:
    components = build_bot_components(
        AppConfig(
            telegram_bot_token="token",
            webhook_secret_path="secret",
            openai_api_key="key",
        )
    )
    assert "style" in components.commands
    response = components.commands["style"].process(1, "")
    assert "brief" in response
    assert "balanced" in response
    assert "detailed" in response


@pytest.mark.parametrize("style", ["brief", "balanced", "detailed"])
def test_style_change_preserves_other_state(style: str) -> None:

    store = UserStateStoreMemory()
    store.set_persona(1, "a pirate")
    store.set_topic(1, "sailing")
    store.append_turn(1, "user", "Hello")
    result = StyleCommandProcessor(store).process(1, "  " + style.upper() + "  ")
    assert style in result
    assert store.get(1).style == style
    assert store.get(1).persona == "a pirate"
    assert store.get(1).topic == "sailing"
    assert store.get(1).history == [{"role": "user", "content": "Hello"}]
    assert store.get(2).style == "brief"
    assert f"Style: {style}" in StatsCommandProcessor(store).process(1, "")


@pytest.mark.parametrize("args", ["", "unknown", "brief detailed"])
def test_invalid_style_shows_options_without_changing_state(args: str) -> None:

    store = UserStateStoreMemory()
    processor = StyleCommandProcessor(store)
    processor.process(1, "balanced")
    response = processor.process(1, args)
    assert "Current style: balanced" in response
    assert "/style brief|balanced|detailed" in response
    assert store.get(1).style == "balanced"


@pytest.mark.parametrize(
    ("style", "guidance"),
    [
        ("brief", "one or two short sentences"),
        ("balanced", "a few sentences"),
        ("detailed", "one or two short paragraphs"),
    ],
)
def test_selected_style_reaches_both_prompts_and_survives_reset(
    run_async, style: str, guidance: str
) -> None:

    store = UserStateStoreMemory()
    store.set_persona(1, "a pirate")
    store.set_topic(1, "sailing")
    StyleCommandProcessor(store).process(1, style)
    llm = MagicMock()
    llm.send = AsyncMock(side_effect=["Ahoy!", "Hello!", "NO_CORRECTION"])
    factory = MagicMock()
    factory.create.return_value = llm
    run_async(StartCommandProcessor(store, factory).process(1, ""))
    run_async(TextMessageProcessor(store, factory).process(1, "Hello"))
    calls = [call.args[0] for call in llm.send.call_args_list]
    for messages in calls[:2]:
        assert guidance in messages[0]["content"]
        assert "a pirate" in messages[0]["content"]
        assert "sailing" in messages[0]["content"]
    assert calls[1][1:] == [
        {"role": "assistant", "content": "Ahoy!"},
        {"role": "user", "content": "Hello"},
    ]
    assert "English teacher" in calls[2][0]["content"]
    assert guidance not in calls[2][0]["content"]
    ResetCommandProcessor(store).process(1, "")
    assert store.get(1).style == style
    assert store.get(1).history == []
