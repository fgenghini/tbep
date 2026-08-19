from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx

try:
    from workers import Response, WorkerEntrypoint
except ModuleNotFoundError:  # Desktop CPython test fallback; Workers supplies these.

    class Response:  # type: ignore[no-redef]
        def __init__(self, body: str, status: int = 200) -> None:
            self.body = body
            self.status = status

    class WorkerEntrypoint:  # type: ignore[no-redef]
        env: Any


from commands.command_processor import CommandProcessor
from commands.help_command_processor import HelpCommandProcessor
from commands.profile_command_processor import ProfileCommandProcessor
from commands.reset_command_processor import ResetCommandProcessor
from commands.start_command_processor import StartCommandProcessor
from commands.stats_command_processor import StatsCommandProcessor
from commands.topic_command_processor import TopicCommandProcessor
from config import AppConfig, load_config
from llm.llm_client_factory import LLMClientFactory
from messages.message_processor import MessageProcessor
from messages.text_message_processor import TextMessageProcessor
from state.user_state_store_memory import UserStateStoreMemory

logger = logging.getLogger(__name__)
EMPTY_PERSONA_REPLY_FALLBACK = (
    "Sorry, I couldn't get a response. Please try again in a moment."
)


@dataclass(frozen=True)
class BotComponents:
    commands: dict[str, CommandProcessor]
    text: TextMessageProcessor


def build_bot_components(config: AppConfig) -> BotComponents:
    store = UserStateStoreMemory()
    factory = LLMClientFactory(
        provider=config.llm_provider,
        openai_api_key=config.openai_api_key,
        openrouter_api_key=config.openrouter_api_key,
        model=config.openrouter_model,
    )
    return BotComponents(
        commands={
            "start": StartCommandProcessor(store, factory),
            "profile": ProfileCommandProcessor(store),
            "topic": TopicCommandProcessor(store),
            "help": HelpCommandProcessor(store),
            "reset": ResetCommandProcessor(store),
            "stats": StatsCommandProcessor(store),
        },
        text=TextMessageProcessor(store, factory),
    )


async def handle_command(
    update: Mapping[str, Any], processor: CommandProcessor, args: str
) -> list[str]:
    user_id = _user_id(update)
    if user_id is None:
        return []
    result = processor.process(user_id, args)
    return [await result if inspect.isawaitable(result) else result]


async def handle_message(
    update: Mapping[str, Any], processor: MessageProcessor
) -> list[str]:
    message = update.get("message")
    user_id = _user_id(update)
    text = message.get("text") if isinstance(message, dict) else None
    if user_id is None or not isinstance(text, str) or not text:
        return []
    result = await processor.process(user_id, text)
    persona_reply = result.get("persona_reply")
    if not isinstance(persona_reply, str):
        return []
    replies = [persona_reply.strip() or EMPTY_PERSONA_REPLY_FALLBACK]
    correction = result.get("correction")
    if isinstance(correction, str) and correction:
        replies.append(correction)
    return replies


def _user_id(update: Mapping[str, Any]) -> int | None:
    message = update.get("message")
    user = message.get("from") if isinstance(message, dict) else None
    value = user.get("id") if isinstance(user, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


class Default(WorkerEntrypoint):
    """Telegram webhook adapter; state is intentionally per warm isolate."""

    components: BotComponents | None = None

    async def fetch(self, request: Any) -> Response:
        config = load_config(_environment(self.env))
        path = "/" + config.webhook_secret_path.strip("/")
        if request.url.split("?", 1)[0].rstrip("/").endswith(path) is False:
            return Response("Not found", status=404)
        if request.method != "POST":
            return Response("Method not allowed", status=405)
        try:
            update = json.loads(await request.text())
        except (TypeError, ValueError):
            return Response("Invalid JSON", status=400)
        if not isinstance(update, dict):
            return Response("Invalid update", status=400)

        if self.components is None:
            self.components = build_bot_components(config)
        replies = await self._dispatch(update)
        try:
            for reply in replies:
                await self._send_telegram(config.telegram_bot_token, update, reply)
        except (httpx.HTTPError, ValueError, KeyError) as error:
            logger.exception("Telegram API request failed")
            return Response(f"Telegram API error: {error}", status=502)
        return Response("ok", status=200)

    async def _dispatch(self, update: dict[str, Any]) -> list[str]:
        if self.components is None:
            return []
        message = update.get("message")
        text = message.get("text") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text:
            return []
        if text.startswith("/"):
            command, _, args = text[1:].partition(" ")
            command = command.split("@", 1)[0].lower()
            processor = self.components.commands.get(command)
            if processor:
                return await handle_command(update, processor, args.strip())
            return []
        return await handle_message(update, self.components.text)

    async def _send_telegram(
        self, token: str, update: dict[str, Any], text: str
    ) -> None:
        message = update.get("message", {})
        chat = message.get("chat", {}) if isinstance(message, dict) else {}
        chat_id = chat.get("id") if isinstance(chat, dict) else None
        if not isinstance(chat_id, (int, str)):
            raise ValueError("Telegram update has no chat id")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise ValueError("Telegram rejected sendMessage")


def _environment(env: Any) -> Mapping[str, str]:
    return {
        name: str(getattr(env, name))
        for name in (
            "TELEGRAM_BOT_TOKEN",
            "LLM_PROVIDER",
            "OPENAI_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENROUTER_MODEL",
            "WEBHOOK_SECRET_PATH",
        )
        if getattr(env, name, None) is not None
    }
