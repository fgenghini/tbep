from typing import Any

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.llm_client import LLMClient


class LLMClientFactory:
    @staticmethod
    def create(provider: str = "chatgpt", **config: Any) -> LLMClient:
        if provider == "chatgpt":
            api_key = config.pop("api_key", "")
            return ChatGPTClient(api_key=api_key, **config)
        raise ValueError(f"Unsupported provider: {provider}")
