import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from telegram.ext import CommandHandler, MessageHandler

from src.commands.command_processor import CommandProcessor
from src.config import AppConfig
from src.main import (
    build_application,
    EMPTY_PERSONA_REPLY_FALLBACK,
    handle_command,
    handle_error,
    handle_message,
    main,
    run_webhook,
)
from src.messages.message_processor import MessageProcessor


def test_handle_command_replies_with_processor_output() -> None:
    update, message = make_update()
    processor = MagicMock(spec=CommandProcessor)
    processor.process.return_value = "profile set"

    asyncio.run(handle_command(update, processor, "a pirate"))

    processor.process.assert_called_once_with(123, "a pirate")
    message.reply_text.assert_awaited_once_with("profile set")


def test_handle_command_supports_empty_args() -> None:
    update, message = make_update()
    processor = MagicMock(spec=CommandProcessor)
    processor.process.return_value = "opening message"

    asyncio.run(handle_command(update, processor, ""))

    processor.process.assert_called_once_with(123, "")
    message.reply_text.assert_awaited_once_with("opening message")


def test_handle_message_sends_persona_reply_and_correction() -> None:
    update, message = make_update(text="I has coffee")
    processor = MagicMock(spec=MessageProcessor)
    processor.process.return_value = {
        "persona_reply": "Nice choice.",
        "correction": "I have coffee.",
    }

    asyncio.run(handle_message(update, processor))

    processor.process.assert_called_once_with(123, "I has coffee")
    assert message.reply_text.await_args_list == [
        call("Nice choice."),
        call("I have coffee."),
    ]


def test_handle_message_omits_correction_when_none() -> None:
    update, message = make_update(text="I am fine")
    processor = MagicMock(spec=MessageProcessor)
    processor.process.return_value = {
        "persona_reply": "That's great.",
        "correction": None,
    }

    asyncio.run(handle_message(update, processor))

    processor.process.assert_called_once_with(123, "I am fine")
    message.reply_text.assert_awaited_once_with("That's great.")


def test_handle_message_sends_fallback_when_persona_reply_is_empty() -> None:
    update, message = make_update(text="hello")
    processor = MagicMock(spec=MessageProcessor)
    processor.process.return_value = {
        "persona_reply": "   ",
        "correction": None,
    }

    asyncio.run(handle_message(update, processor))

    processor.process.assert_called_once_with(123, "hello")
    message.reply_text.assert_awaited_once_with(EMPTY_PERSONA_REPLY_FALLBACK)


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
    assert len(registered) == 7
    assert isinstance(registered[0], CommandHandler)
    assert registered[0].commands == frozenset({"start"})
    assert registered[1].commands == frozenset({"profile"})
    assert registered[2].commands == frozenset({"topic"})
    assert registered[3].commands == frozenset({"help"})
    assert registered[4].commands == frozenset({"reset"})
    assert registered[5].commands == frozenset({"stats"})
    assert isinstance(registered[6], MessageHandler)
    assert str(registered[6].filters) == "<filters.TEXT and <inverted filters.COMMAND>>"
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


def test_run_webhook_errors_when_webhook_url_is_not_configured() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
    )
    application = MagicMock()

    with pytest.raises(
        RuntimeError,
        match="Missing required environment variable: WEBHOOK_BASE_URL",
    ):
        run_webhook(application, config)

    application.run_webhook.assert_not_called()


def test_main_errors_when_webhook_url_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.delenv("WEBHOOK_BASE_URL", raising=False)

    with pytest.raises(
        RuntimeError,
        match="Missing required environment variable: WEBHOOK_BASE_URL",
    ):
        main()


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
