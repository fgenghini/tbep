from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TypedDict


class HistoryEntry(TypedDict):
    role: str
    content: str


@dataclass
class UserState:
    persona: str = ""
    topic: str = ""
    history: list[HistoryEntry] = field(default_factory=list)


class UserStateStore(ABC):
    @abstractmethod
    def get(self, user_id: int) -> UserState:
        raise NotImplementedError

    @abstractmethod
    def set_persona(self, user_id: int, persona: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_topic(self, user_id: int, topic: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset_history(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_turn(self, user_id: int, role: str, content: str) -> None:
        raise NotImplementedError
