from __future__ import annotations

import logging
import os
from collections.abc import Callable, Coroutine
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

from src.commands.help_command_processor import HelpCommandProcessor
from src.commands.profile_command_processor import ProfileCommandProcessor
from src.commands.reset_command_processor import ResetCommandProcessor
from src.commands.start_command_processor import StartCommandProcessor
from src.commands.topic_command_processor import TopicCommandProcessor
from src.config import AppConfig, load_config
from src.llm.llm_client_factory import LLMClientFactory
from src.messages.text_message_processor import TextMessageProcessor
from src.state.user_state_store_memory import UserStateStoreMemory

logger = logging.getLogger(__name__)

PUBLIC_WEBHOOK_ENV_VARS = (
    "RAILWAY_PUBLIC_DOMAIN",
    "RAILWAY_PUBLIC_URL",
    "PUBLIC_URL",
    "WEBHOOK_BASE_URL",
)


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
    llm_client_factory = LLMClientFactory()
    llm_config = {"api_key": config.openai_api_key}

    return BotComponents(
        start=StartCommandProcessor(user_state_store, llm_client_factory, **llm_config),
        profile=ProfileCommandProcessor(
            user_state_store, llm_client_factory, **llm_config
        ),
        topic=TopicCommandProcessor(user_state_store, llm_client_factory, **llm_config),
        help=HelpCommandProcessor(user_state_store),
        reset=ResetCommandProcessor(user_state_store, llm_client_factory, **llm_config),
        text=TextMessageProcessor(user_state_store, llm_client_factory, **llm_config),
    )


def register_handlers(
    application: Application[Any, Any, Any, Any, Any, Any],
    components: BotComponents,
) -> None:
    application.add_handler(
        CommandHandler("start", make_start_callback(components.start))
    )
    application.add_handler(
        CommandHandler("profile", make_profile_callback(components.profile))
    )
    application.add_handler(
        CommandHandler("topic", make_topic_callback(components.topic))
    )
    application.add_handler(CommandHandler("help", make_help_callback(components.help)))
    application.add_handler(
        CommandHandler("reset", make_reset_callback(components.reset))
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            make_text_callback(components.text),
        )
    )


def make_start_callback(
    processor: StartCommandProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_start_command(update, context, processor)

    return callback


def make_profile_callback(
    processor: ProfileCommandProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_profile_command(update, context, processor)

    return callback


def make_topic_callback(
    processor: TopicCommandProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_topic_command(update, context, processor)

    return callback


def make_help_callback(
    processor: HelpCommandProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_help_command(update, context, processor)

    return callback


def make_reset_callback(
    processor: ResetCommandProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_reset_command(update, context, processor)

    return callback


def make_text_callback(
    processor: TextMessageProcessor,
) -> Callable[[Update, Any], Coroutine[Any, Any, None]]:
    async def callback(update: Update, context: Any) -> None:
        await handle_text_message(update, context, processor)

    return callback


async def handle_start_command(
    update: Update, context: Any, processor: StartCommandProcessor
) -> None:
    await _reply_command(update, processor, "")


async def handle_profile_command(
    update: Update,
    context: Any,
    processor: ProfileCommandProcessor,
) -> None:
    await _reply_command(update, processor, _join_context_args(context))


async def handle_topic_command(
    update: Update,
    context: Any,
    processor: TopicCommandProcessor,
) -> None:
    await _reply_command(update, processor, _join_context_args(context))


async def handle_help_command(
    update: Update,
    context: Any,
    processor: HelpCommandProcessor,
) -> None:
    await _reply_command(update, processor, "")


async def handle_reset_command(
    update: Update,
    context: Any,
    processor: ResetCommandProcessor,
) -> None:
    await _reply_command(update, processor, "")


async def handle_text_message(
    update: Update, context: Any, processor: TextMessageProcessor
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


async def _reply_command(
    update: Update,
    processor: HelpCommandProcessor
    | ProfileCommandProcessor
    | ResetCommandProcessor
    | StartCommandProcessor
    | TopicCommandProcessor,
    args: str,
) -> None:
    message = update.message
    user_id = _get_user_id(update)
    if message is None or user_id is None:
        return

    response = processor.process(user_id, args)
    await message.reply_text(response)


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


def _build_webhook_url(config: AppConfig) -> str | None:
    base_url = _get_public_base_url()
    if base_url is None:
        return None

    return f"{base_url.rstrip('/')}/{config.webhook_secret_path.lstrip('/')}"


def _get_public_base_url() -> str | None:
    for env_var in PUBLIC_WEBHOOK_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            if value.startswith("http://") or value.startswith("https://"):
                return value
            return f"https://{value}"
    return None


def run_webhook(
    application: Application[Any, Any, Any, Any, Any, Any],
    config: AppConfig,
) -> None:
    webhook_url = _build_webhook_url(config)
    if webhook_url is not None:
        application.run_webhook(
            listen="0.0.0.0",
            port=config.port,
            url_path=config.webhook_secret_path,
            webhook_url=webhook_url,
        )
        return

    application.run_webhook(
        listen="0.0.0.0",
        port=config.port,
        url_path=config.webhook_secret_path,
    )


if __name__ == "__main__":
    main()
