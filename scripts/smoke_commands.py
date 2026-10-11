"""Exercise Telegram commands through the Worker without external API calls."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from commands.help_command_processor import HELP_TEXT  # noqa: E402
from commands.profile_command_processor import PROFILE_UPDATED_MESSAGE  # noqa: E402
from commands.reset_command_processor import RESET_MESSAGE  # noqa: E402
from commands.topic_command_processor import TOPIC_UPDATED_MESSAGE  # noqa: E402
from main import Default  # noqa: E402

OPENING = "Smoke test opening"


class FakeLLM:
    async def send(self, messages: list[dict[str, str]]) -> str:
        if len(messages) != 1 or messages[0]["role"] != "system":
            raise AssertionError("The command smoke test made an unexpected model call")
        return OPENING


class Request:
    def __init__(self, update: dict[str, Any], *, method: str = "POST") -> None:
        self.url = "https://localhost/smoke-secret"
        self.method = method
        self.update = update

    async def text(self) -> str:
        return json.dumps(self.update)


def update(command: str, user_id: int = 123) -> dict[str, Any]:
    return {
        "message": {
            "from": {"id": user_id},
            "chat": {"id": user_id},
            "text": command,
        }
    }


async def main() -> None:
    worker = Default()
    worker.env = SimpleNamespace(
        TELEGRAM_BOT_TOKEN="smoke-token",
        OPENAI_API_KEY="smoke-key",
        WEBHOOK_SECRET_PATH="smoke-secret",
    )
    replies: list[str] = []

    async def capture_send(
        self: Default, token: str, message: dict[str, Any], text: str
    ) -> None:
        assert token == "smoke-token"
        assert message["message"]["chat"]["id"] in (123, 456)
        replies.append(text)

    async def check(command: str, expected: str, user_id: int = 123) -> None:
        replies.clear()
        response = await worker.fetch(Request(update(command, user_id)))
        assert response.status == 200, (command, response.status)
        assert replies == [expected], (command, replies)
        print(f"PASS {command}")

    with (
        patch("llm.llm_client_factory.LLMClientFactory.create", return_value=FakeLLM()),
        patch.object(Default, "_send_telegram", capture_send),
    ):
        await check("/help", HELP_TEXT)
        await check("/profile a pirate", PROFILE_UPDATED_MESSAGE)
        await check("/topic sailing", TOPIC_UPDATED_MESSAGE)
        await check("/stats", "Persona: a pirate\nTopic: sailing\nMessages stored: 0")
        await check("/start", f"You can use /help for details.\n\n{OPENING}")
        await check("/stats", "Persona: a pirate\nTopic: sailing\nMessages stored: 1")
        await check("/reset", RESET_MESSAGE)
        await check("/stats", "Persona: a pirate\nTopic: sailing\nMessages stored: 0")
        await check("/start", f"You can use /help for details.\n\n{OPENING}", 456)
        await check(
            "/stats",
            "Persona: a casual American person\n"
            "Topic: casual daily conversation\nMessages stored: 1",
            456,
        )

    print("Command smoke test passed; no network requests or model tokens used.")


if __name__ == "__main__":
    asyncio.run(main())
