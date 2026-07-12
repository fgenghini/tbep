import os
from typing import Any

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.gemma_openrouter_client import GemmaOpenRouterClient
from src.llm.llm_client import LLMClient

DEFAULT_PROVIDER = "chatgpt"
PROVIDER_ENV_VAR = "LLM_PROVIDER"
GEMMA_OPENROUTER_PROVIDER = "gemma-openrouter"


class LLMClientFactory:
    def __init__(self, **config: Any) -> None:
        self.config = config

    def create(self) -> LLMClient:
        config = self.config.copy()
        provider = (
            config.pop("provider", None)
            or os.getenv(PROVIDER_ENV_VAR, DEFAULT_PROVIDER).strip()
            or DEFAULT_PROVIDER
        )

        if provider == "chatgpt":
            api_key = config.pop("api_key", None) or config.pop("openai_api_key", "")
            return ChatGPTClient(api_key=api_key, **config)
        if provider == GEMMA_OPENROUTER_PROVIDER:
            api_key = config.pop("openrouter_api_key", None) or config.pop(
                "api_key", ""
            )
            return GemmaOpenRouterClient(api_key=api_key, **config)
        raise ValueError(f"Unsupported provider: {provider}")
