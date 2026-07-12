import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from telegram.ext import CommandHandler, MessageHandler

from src.commands.command_processor import CommandProcessor
from src.config import AppConfig
from src.main import (
    build_application,
    handle_error,
    make_command_callback,
    make_message_callback,
    run_webhook,
)
from src.messages.message_processor import MessageProcessor


def test_make_command_callback_uses_args_provider() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=["a", "pirate"])
    processor = MagicMock(spec=CommandProcessor)
    processor.process.return_value = "profile set"
    callback = make_command_callback(processor, lambda ctx: " ".join(ctx.args))

    asyncio.run(callback(update, context))

    processor.process.assert_called_once_with(123, "a pirate")
    message.reply_text.assert_awaited_once_with("profile set")


def test_make_command_callback_supports_empty_args() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=[])
    processor = MagicMock(spec=CommandProcessor)
    processor.process.return_value = "opening message"
    callback = make_command_callback(processor, lambda _ctx: "")

    asyncio.run(callback(update, context))

    processor.process.assert_called_once_with(123, "")
    message.reply_text.assert_awaited_once_with("opening message")


def test_make_message_callback_sends_persona_reply_and_correction() -> None:
    update, message = make_update(text="I has coffee")
    context = SimpleNamespace()
    processor = MagicMock(spec=MessageProcessor)
    processor.process.return_value = {
        "persona_reply": "Nice choice.",
        "correction": "I have coffee.",
    }
    callback = make_message_callback(processor)

    asyncio.run(callback(update, context))

    processor.process.assert_called_once_with(123, "I has coffee")
    assert message.reply_text.await_args_list == [
        call("Nice choice."),
        call("I have coffee."),
    ]


def test_make_message_callback_omits_correction_when_none() -> None:
    update, message = make_update(text="I am fine")
    context = SimpleNamespace()
    processor = MagicMock(spec=MessageProcessor)
    processor.process.return_value = {
        "persona_reply": "That's great.",
        "correction": None,
    }
    callback = make_message_callback(processor)

    asyncio.run(callback(update, context))

    processor.process.assert_called_once_with(123, "I am fine")
    message.reply_text.assert_awaited_once_with("That's great.")


def test_handle_error_logs_exception(caplog: pytest.LogCaptureFixture) -> None:
    context = SimpleNamespace(error=RuntimeError("boom"))

    with caplog.at_level("ERROR"):
        asyncio.run(handle_error(object(), context))

    assert any("boom" in record.message for record in caplog.records)


def test_build_application_registers_expected_handlers() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
    )

    application = build_application(config)

    registered = application.handlers[0]
    assert len(registered) == 6
    assert isinstance(registered[0], CommandHandler)
    assert registered[0].commands == frozenset({"start"})
    assert registered[1].commands == frozenset({"profile"})
    assert registered[2].commands == frozenset({"topic"})
    assert registered[3].commands == frozenset({"help"})
    assert registered[4].commands == frozenset({"reset"})
    assert isinstance(registered[5], MessageHandler)
    assert str(registered[5].filters) == "<filters.TEXT and <inverted filters.COMMAND>>"
    assert len(application.error_handlers) == 1


def test_run_webhook_uses_configured_webhook_url() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
        webhook_base_url="https://example.com",
    )
    application = MagicMock()

    run_webhook(application, config)

    application.run_webhook.assert_called_once_with(
        listen="0.0.0.0",
        port=9000,
        url_path="secret-path",
        webhook_url="https://example.com/secret-path",
    )


def test_run_webhook_omits_webhook_url_when_not_configured() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
    )
    application = MagicMock()

    run_webhook(application, config)

    application.run_webhook.assert_called_once_with(
        listen="0.0.0.0",
        port=9000,
        url_path="secret-path",
    )


def make_update(
    text: str | None = "hello",
) -> tuple[SimpleNamespace, MagicMock]:
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.text = text
    update = SimpleNamespace(
        message=message,
        effective_user=SimpleNamespace(id=123),
    )
    return update, message
