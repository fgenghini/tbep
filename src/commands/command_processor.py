from abc import ABC, abstractmethod

from src.state.user_state_store import UserStateStore


class CommandProcessor(ABC):
    def __init__(self, user_state_store: UserStateStore) -> None:
        self.user_state_store = user_state_store

    @abstractmethod
    def process(self, user_id: int, args: str) -> str:
        raise NotImplementedError
