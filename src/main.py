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
from commands.feedback_command_processor import FeedbackCommandProcessor
from commands.help_command_processor import HelpCommandProcessor
from commands.profile_command_processor import ProfileCommandProcessor
from commands.reset_command_processor import ResetCommandProcessor
from commands.start_command_processor import StartCommandProcessor
from commands.stats_command_processor import StatsCommandProcessor
from commands.style_command_processor import StyleCommandProcessor
from commands.topic_command_processor import TopicCommandProcessor
from config import AppConfig, load_config
from llm.llm_client_factory import LLMClientFactory
from messages.message_processor import MessageProcessor
from messages.rephrase_processor import EXPIRED_MESSAGE, RephraseProcessor
from messages.text_message_processor import TextMessageProcessor
from state.user_state_store_memory import UserStateStoreMemory

logger = logging.getLogger(__name__)
EMPTY_PERSONA_REPLY_FALLBACK = (
    "Sorry, I couldn't get a response. Please try again in a moment."
)


@dataclass(frozen=True)
class TelegramReply:
    text: str
    reply_markup: dict[str, Any] | None = None


@dataclass(frozen=True)
class BotComponents:
    commands: dict[str, CommandProcessor]
    text: TextMessageProcessor
    rephrase: RephraseProcessor


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
            "feedback": FeedbackCommandProcessor(store),
            "style": StyleCommandProcessor(store),
        },
        text=TextMessageProcessor(store, factory),
        rephrase=RephraseProcessor(store, factory),
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
) -> list[TelegramReply]:
    message = update.get("message")
    user_id = _user_id(update)
    text = message.get("text") if isinstance(message, dict) else None
    if user_id is None or not isinstance(text, str) or not text:
        return []
    result = await processor.process(user_id, text)
    persona_reply = result.get("persona_reply")
    if not isinstance(persona_reply, str):
        return []
    markup = None
    token = result.get("rephrase_token")
    if isinstance(token, str) and isinstance(processor, TextMessageProcessor):
        context = processor.user_state_store.get(user_id).latest_sentence
        chat_id = _chat_id(update)
        if context is not None and context.token == token and chat_id is not None:
            context.chat_id = chat_id
            markup = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Say it another way",
                            "callback_data": f"rephrase:{token}",
                        }
                    ]
                ]
            }
    replies = [
        TelegramReply(persona_reply.strip() or EMPTY_PERSONA_REPLY_FALLBACK, markup)
    ]
    correction = result.get("correction")
    if isinstance(correction, str) and correction:
        replies.append(TelegramReply(correction))
    return replies


def _user_id(update: Mapping[str, Any]) -> int | None:
    message = update.get("message")
    user = message.get("from") if isinstance(message, dict) else None
    value = user.get("id") if isinstance(user, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _chat_id(update: Mapping[str, Any]) -> int | str | None:
    query = update.get("callback_query")
    message = query.get("message") if isinstance(query, dict) else update.get("message")
    chat = message.get("chat") if isinstance(message, dict) else None
    value = chat.get("id") if isinstance(chat, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    return value


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
        try:
            if isinstance(update.get("callback_query"), dict):
                replies = await self._handle_callback(config.telegram_bot_token, update)
            else:
                replies = await self._dispatch(update)
            for reply in replies:
                if reply.reply_markup is None:
                    await self._send_telegram(
                        config.telegram_bot_token, update, reply.text
                    )
                else:
                    await self._send_telegram(
                        config.telegram_bot_token,
                        update,
                        reply.text,
                        reply.reply_markup,
                    )
        except (httpx.HTTPError, ValueError, KeyError) as error:
            logger.exception("Telegram API request failed")
            return Response(f"Telegram API error: {error}", status=502)
        return Response("ok", status=200)

    async def _dispatch(self, update: dict[str, Any]) -> list[TelegramReply]:
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
                return [
                    TelegramReply(text)
                    for text in await handle_command(update, processor, args.strip())
                ]
            return []
        return await handle_message(update, self.components.text)

    async def _handle_callback(
        self, token: str, update: dict[str, Any]
    ) -> list[TelegramReply]:
        query = update["callback_query"]
        query_id = query.get("id")
        if not isinstance(query_id, str) or not query_id:
            return []
        data = query.get("data")
        known = (
            isinstance(data, str)
            and data.startswith("rephrase:")
            and len(data) > len("rephrase:")
        )
        user = query.get("from")
        user_id = user.get("id") if isinstance(user, dict) else None
        chat_id = _chat_id(update)
        valid = (
            isinstance(user_id, int)
            and not isinstance(user_id, bool)
            and chat_id is not None
            and self.components is not None
        )
        payload: dict[str, Any] = {"callback_query_id": query_id}
        if known and not valid:
            payload["text"] = EXPIRED_MESSAGE
        await self._telegram_request(token, "answerCallbackQuery", payload)
        if not known or not valid:
            return []
        # The checks above narrow values at runtime; keep explicit type guards here.
        if not isinstance(data, str) or not isinstance(user_id, int):
            return []
        if self.components is None or chat_id is None:
            return []
        reply = await self.components.rephrase.process(
            user_id, chat_id, data.removeprefix("rephrase:")
        )
        return [TelegramReply(reply)]

    async def _send_telegram(
        self,
        token: str,
        update: dict[str, Any],
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        chat_id = _chat_id(update)
        if chat_id is None:
            raise ValueError("Telegram update has no chat id")
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        await self._telegram_request(token, "sendMessage", payload)

    async def _telegram_request(
        self, token: str, method: str, payload: dict[str, Any]
    ) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{token}/{method}",
                json=payload,
            )
            response.raise_for_status()
            if not response.json().get("ok"):
                raise ValueError(f"Telegram rejected {method}")


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
