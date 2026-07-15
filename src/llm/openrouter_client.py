from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.llm.llm_client import LLMClient

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL_ENV_VAR = "OPENROUTER_MODEL"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"


class OpenRouterClientError(Exception):
    pass


class OpenRouterClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None, **config: Any) -> None:
        super().__init__(api_key, model, **config)
        self.model_name = (
            model
            or os.getenv(OPENROUTER_MODEL_ENV_VAR, DEFAULT_OPENROUTER_MODEL).strip()
            or DEFAULT_OPENROUTER_MODEL
        )
        self.reasoning_enabled = bool(config.get("reasoning_enabled", True))
        self.timeout = float(config.get("timeout", 30))

    def send(self, messages: list[dict[str, str]]) -> str:
        try:
            payload = self._build_request_payload(messages)
            response = self._call_api(payload)
            return self._parse_response(response)
        except (
            KeyError,
            TypeError,
            ValueError,
            urllib.error.URLError,
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

    def _call_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            OPENROUTER_CHAT_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        parsed: dict[str, Any] = json.loads(body)
        return parsed

    def _parse_response(self, response: dict[str, Any]) -> str:
        choices = response.get("choices", [])
        if not choices:
            return ""
        content = choices[0].get("message", {}).get("content")
        return content if isinstance(content, str) else ""
