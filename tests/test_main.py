import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from telegram.ext import CommandHandler, MessageHandler

from src.config import AppConfig
from src.main import (
    build_application,
    handle_error,
    handle_help_command,
    handle_profile_command,
    handle_reset_command,
    handle_start_command,
    handle_text_message,
    handle_topic_command,
    run_webhook,
)


def test_handle_start_command_replies_with_processor_output() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=["ignored"])
    processor = MagicMock()
    processor.process.return_value = "opening message"

    asyncio.run(handle_start_command(update, context, processor))

    processor.process.assert_called_once_with(123, "")
    message.reply_text.assert_awaited_once_with("opening message")


def test_handle_profile_command_joins_context_args() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=["a", "pirate"])
    processor = MagicMock()
    processor.process.return_value = "profile set"

    asyncio.run(handle_profile_command(update, context, processor))

    processor.process.assert_called_once_with(123, "a pirate")
    message.reply_text.assert_awaited_once_with("profile set")


def test_handle_topic_command_joins_context_args() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=["ordering", "coffee"])
    processor = MagicMock()
    processor.process.return_value = "topic set"

    asyncio.run(handle_topic_command(update, context, processor))

    processor.process.assert_called_once_with(123, "ordering coffee")
    message.reply_text.assert_awaited_once_with("topic set")


def test_handle_help_command_replies_with_help_text() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=[])
    processor = MagicMock()
    processor.process.return_value = "help text"

    asyncio.run(handle_help_command(update, context, processor))

    processor.process.assert_called_once_with(123, "")
    message.reply_text.assert_awaited_once_with("help text")


def test_handle_reset_command_replies_with_opening_message() -> None:
    update, message = make_update()
    context = SimpleNamespace(args=[])
    processor = MagicMock()
    processor.process.return_value = "reset opening"

    asyncio.run(handle_reset_command(update, context, processor))

    processor.process.assert_called_once_with(123, "")
    message.reply_text.assert_awaited_once_with("reset opening")


def test_handle_text_message_sends_persona_reply_and_correction() -> None:
    update, message = make_update(text="I has coffee")
    context = SimpleNamespace()
    processor = MagicMock()
    processor.process.return_value = {
        "persona_reply": "Nice choice.",
        "correction": "I have coffee.",
    }

    asyncio.run(handle_text_message(update, context, processor))

    processor.process.assert_called_once_with(123, "I has coffee")
    assert message.reply_text.await_args_list == [
        call("Nice choice."),
        call("I have coffee."),
    ]


def test_handle_text_message_omits_correction_when_none() -> None:
    update, message = make_update(text="I am fine")
    context = SimpleNamespace()
    processor = MagicMock()
    processor.process.return_value = {
        "persona_reply": "That's great.",
        "correction": None,
    }

    asyncio.run(handle_text_message(update, context, processor))

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


def test_run_webhook_uses_public_domain_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "example.railway.app")
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
        webhook_url="https://example.railway.app/secret-path",
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
