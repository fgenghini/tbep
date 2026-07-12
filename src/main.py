from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.commands.command_processor import CommandProcessor
from src.commands.help_command_processor import HelpCommandProcessor
from src.commands.profile_command_processor import ProfileCommandProcessor
from src.commands.reset_command_processor import ResetCommandProcessor
from src.commands.start_command_processor import StartCommandProcessor
from src.commands.topic_command_processor import TopicCommandProcessor
from src.config import AppConfig, ConfigError, load_config
from src.llm.llm_client_factory import LLMClientFactory
from src.messages.message_processor import MessageProcessor
from src.messages.text_message_processor import TextMessageProcessor
from src.state.user_state_store_memory import UserStateStoreMemory

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BotComponents:
    start: StartCommandProcessor
    profile: ProfileCommandProcessor
    topic: TopicCommandProcessor
    help: HelpCommandProcessor
    reset: ResetCommandProcessor
    text: TextMessageProcessor


def main() -> None:
    config = load_config()
    if config.webhook_url is None:
        raise ConfigError("Missing required environment variable: WEBHOOK_BASE_URL")

    application = build_application(config)
    run_webhook(application, config)


def build_application(
    config: AppConfig,
) -> Application[Any, Any, Any, Any, Any, Any]:
    components = build_bot_components(config)
    application = ApplicationBuilder().token(config.telegram_bot_token).build()
    register_handlers(application, components)
    application.add_error_handler(handle_error)
    return application


def build_bot_components(config: AppConfig) -> BotComponents:
    user_state_store = UserStateStoreMemory()
    llm_client_factory = LLMClientFactory(
        provider=config.llm_provider,
        openai_api_key=config.openai_api_key,
        openrouter_api_key=config.openrouter_api_key,
    )

    return BotComponents(
        start=StartCommandProcessor(user_state_store, llm_client_factory),
        profile=ProfileCommandProcessor(user_state_store, llm_client_factory),
        topic=TopicCommandProcessor(user_state_store, llm_client_factory),
        help=HelpCommandProcessor(user_state_store),
        reset=ResetCommandProcessor(user_state_store, llm_client_factory),
        text=TextMessageProcessor(user_state_store, llm_client_factory),
    )


def register_handlers(
    application: Application[Any, Any, Any, Any, Any, Any],
    components: BotComponents,
) -> None:
    application.add_handler(
        CommandHandler(
            "start",
            lambda update, context: handle_command(update, components.start, ""),
        )
    )
    application.add_handler(
        CommandHandler(
            "profile",
            lambda update, context: handle_command(
                update, components.profile, _join_context_args(context)
            ),
        )
    )
    application.add_handler(
        CommandHandler(
            "topic",
            lambda update, context: handle_command(
                update, components.topic, _join_context_args(context)
            ),
        )
    )
    application.add_handler(
        CommandHandler(
            "help",
            lambda update, context: handle_command(update, components.help, ""),
        )
    )
    application.add_handler(
        CommandHandler(
            "reset",
            lambda update, context: handle_command(update, components.reset, ""),
        )
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lambda update, context: handle_message(update, components.text),
        )
    )


async def handle_command(
    update: Update,
    processor: CommandProcessor,
    args: str,
) -> None:
    message = update.message
    user_id = _get_user_id(update)
    if message is None or user_id is None:
        return

    response = processor.process(user_id, args)
    await message.reply_text(response)


async def handle_message(
    update: Update,
    processor: MessageProcessor,
) -> None:
    message = update.message
    user_id = _get_user_id(update)
    if message is None or user_id is None or message.text is None:
        return

    result = processor.process(user_id, message.text)
    persona_reply = result["persona_reply"]
    if not isinstance(persona_reply, str):
        return

    await message.reply_text(persona_reply)
    correction = result.get("correction")
    if isinstance(correction, str) and correction:
        await message.reply_text(correction)


async def handle_error(update: object, context: Any) -> None:
    error = getattr(context, "error", None)
    if error is None:
        logger.error("Unhandled exception while processing update")
        return

    logger.error(
        "Unhandled exception while processing update: %s",
        error,
        exc_info=(type(error), error, error.__traceback__),
    )


def _join_context_args(context: Any) -> str:
    args = getattr(context, "args", [])
    if not args:
        return ""
    return " ".join(args).strip()


def _get_user_id(update: Update) -> int | None:
    user = update.effective_user
    if user is None:
        return None
    return user.id


def run_webhook(
    application: Application[Any, Any, Any, Any, Any, Any],
    config: AppConfig,
) -> None:
    if config.webhook_url is None:
        raise ConfigError("Missing required environment variable: WEBHOOK_BASE_URL")

    application.run_webhook(
        listen="0.0.0.0",
        port=config.port,
        url_path=config.webhook_secret_path,
        webhook_url=config.webhook_url,
    )


if __name__ == "__main__":
    main()
