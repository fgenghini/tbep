import os
from typing import Any

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.llm_client import LLMClient

DEFAULT_PROVIDER = "chatgpt"
PROVIDER_ENV_VAR = "LLM_PROVIDER"


class LLMClientFactory:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def create(self) -> LLMClient:
        provider = (
            os.getenv(PROVIDER_ENV_VAR, DEFAULT_PROVIDER).strip() or DEFAULT_PROVIDER
        )
        config = self.config.copy()

        if provider == "chatgpt":
            api_key = config.pop("api_key", "")
            return ChatGPTClient(api_key=api_key, **config)
        raise ValueError(f"Unsupported provider: {provider}")
