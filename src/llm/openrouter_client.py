from __future__ import annotations

import os
from typing import Any

import httpx

from src.llm.llm_client import LLMClient

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "OPENROUTER_MODEL"
DEFAULT_OPENROUTER_MODEL = "google/gemma-4-31b-it:free"


class OpenRouterClientError(Exception):
    pass


class OpenRouterClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None, **config: Any) -> None:
        super().__init__(api_key, model, **config)
        self.model_name = (
            model or os.getenv(OPENROUTER_MODEL, DEFAULT_OPENROUTER_MODEL).strip()
        )
        self.reasoning_enabled = bool(config.get("reasoning_enabled", True))
        self.timeout = float(config.get("timeout", 30))

    async def send(self, messages: list[dict[str, str]]) -> str:
        try:
            payload = self._build_request_payload(messages)
            response = await self._call_api(payload)
            return self._parse_response(response)
        except (
            KeyError,
            TypeError,
            ValueError,
            httpx.HTTPError,
        ) as e:
            raise OpenRouterClientError(f"OpenRouter API Error: {e}") from e

    def _build_request_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
        }
        if self.reasoning_enabled:
            payload["reasoning"] = {"enabled": True}
        return payload

    async def _call_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                OPENROUTER_CHAT_COMPLETIONS_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            parsed: dict[str, Any] = response.json()
            return parsed

    def _parse_response(self, response: dict[str, Any]) -> str:
        choices = response.get("choices", [])
        if not choices:
            return ""
        content = choices[0].get("message", {}).get("content")
        return content if isinstance(content, str) else ""
