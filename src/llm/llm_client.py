from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    def __init__(self, api_key: str, model: str | None = None, **config: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.config = config

    @abstractmethod
    def send(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError
