from __future__ import annotations

from typing import Any

import openai
from openai.types.chat import ChatCompletion

from src.llm.llm_client import LLMClient


class ChatGPTClientError(Exception):
    pass


class ChatGPTClient(LLMClient):
    def __init__(self, api_key: str, model: str | None = None, **config: Any) -> None:
        super().__init__(api_key, model, **config)
        self.model_name = model or "gpt-4o-mini"
        self._client = openai.OpenAI(api_key=api_key)

    def send(self, messages: list[dict[str, str]]) -> str:
        try:
            payload = self._build_request_payload(messages)
            response = self._call_api(payload)
            return self._parse_response(response)
        except openai.OpenAIError as e:
            raise ChatGPTClientError(f"OpenAI API Error: {e}") from e

    def _build_request_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": messages,
        }

    def _call_api(self, payload: dict[str, Any]) -> ChatCompletion:
        return self._client.chat.completions.create(
            model=str(payload["model"]),
            messages=payload["messages"],
        )

    def _parse_response(self, response: ChatCompletion) -> str:
        if not response.choices:
            return ""
        content = response.choices[0].message.content
        return content if content is not None else ""
