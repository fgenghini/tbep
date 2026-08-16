import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import EMPTY_PERSONA_REPLY_FALLBACK, Default, handle_message


def update(text: str = "hello") -> dict:
    return {
        "message": {
            "from": {"id": 123},
            "chat": {"id": 123},
            "text": text,
        }
    }


def request(body: object, method: str = "POST") -> MagicMock:
    result = MagicMock()
    result.method = method
    result.url = "https://tbep.example/secret"
    result.text = AsyncMock(return_value=json.dumps(body))
    return result


def worker() -> Default:
    instance = Default()
    instance.env = MagicMock(
        TELEGRAM_BOT_TOKEN="token",
        OPENAI_API_KEY="key",
        WEBHOOK_SECRET_PATH="secret",
    )
    return instance


def test_message_sends_persona_and_correction_separately() -> None:
    processor = MagicMock()
    processor.process = AsyncMock(
        return_value={"persona_reply": "Nice.", "correction": "I have coffee."}
    )
    result = asyncio.run(handle_message(update("I has coffee"), processor))
    assert result == ["Nice.", "I have coffee."]


def test_empty_persona_reply_uses_fallback() -> None:
    processor = MagicMock()
    processor.process = AsyncMock(
        return_value={"persona_reply": "  ", "correction": None}
    )
    assert asyncio.run(handle_message(update(), processor)) == [
        EMPTY_PERSONA_REPLY_FALLBACK
    ]


def test_worker_rejects_wrong_method_and_path() -> None:
    instance = worker()
    assert asyncio.run(instance.fetch(request(update(), "GET"))).status == 405
    bad = request(update())
    bad.url = "https://tbep.example/nope"
    assert asyncio.run(instance.fetch(bad)).status == 404


@patch("src.main.Default._send_telegram", new_callable=AsyncMock)
def test_worker_dispatches_plain_text(mock_send: AsyncMock) -> None:
    instance = worker()
    instance.components = MagicMock()
    instance.components.text.process = AsyncMock(
        return_value={"persona_reply": "Hello", "correction": None}
    )
    result = asyncio.run(instance.fetch(request(update())))
    assert result.status == 200
    mock_send.assert_awaited_once_with("token", update(), "Hello")
