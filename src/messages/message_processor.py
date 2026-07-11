from abc import ABC, abstractmethod
from typing import Any, Protocol

from src.llm.llm_client import LLMClient
from src.state.user_state_store import UserStateStore


class LLMClientFactoryProtocol(Protocol):
    def create(self, **config: Any) -> LLMClient: ...


class MessageProcessor(ABC):
    def __init__(
        self,
        user_state_store: UserStateStore,
        llm_client_factory: LLMClientFactoryProtocol,
        **llm_config: Any,
    ) -> None:
        self.user_state_store = user_state_store
        self.llm_client = llm_client_factory.create(**llm_config)

    @abstractmethod
    def process(self, user_id: int, content: str) -> dict[str, str | None]:
        raise NotImplementedError
