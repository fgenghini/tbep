import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.llm.openrouter_client import (
    DEFAULT_OPENROUTER_MODEL,
    OpenRouterClient,
    OpenRouterClientError,
)


def test_build_request_payload_defaults_to_openrouter_model_with_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    client = OpenRouterClient(api_key="fake-key")
    assert client._build_request_payload([]) == {
        "model": DEFAULT_OPENROUTER_MODEL,
        "messages": [],
        "reasoning": {"enabled": True},
    }


def test_parse_response() -> None:
    client = OpenRouterClient(api_key="fake-key")
    assert client._parse_response({"choices": [{"message": {"content": "ok"}}]}) == "ok"


def test_send_uses_async_http() -> None:
    response = MagicMock()
    response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    response.raise_for_status = MagicMock()
    client = OpenRouterClient(api_key="fake-key")
    fake_http = MagicMock()
    fake_http.__aenter__ = AsyncMock(return_value=fake_http)
    fake_http.__aexit__ = AsyncMock(return_value=None)
    fake_http.post = AsyncMock(return_value=response)

    async def run() -> str:
        client_module = __import__("src.llm.openrouter_client", fromlist=["httpx"])
        original = client_module.httpx.AsyncClient
        client_module.httpx.AsyncClient = MagicMock(return_value=fake_http)
        try:
            return await client.send([{"role": "user", "content": "hi"}])
        finally:
            client_module.httpx.AsyncClient = original

    assert asyncio.run(run()) == "ok"
    fake_http.post.assert_awaited_once()


def test_send_error_is_wrapped() -> None:
    client = OpenRouterClient(api_key="fake-key")
    client._call_api = AsyncMock(side_effect=ValueError("bad response"))
    with pytest.raises(OpenRouterClientError, match="OpenRouter API Error:"):
        asyncio.run(client.send([]))
