from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, TypedDict

FeedbackMode = Literal["off", "important", "all"]

ReplyStyle = Literal["brief", "balanced", "detailed"]


class HistoryEntry(TypedDict):
    role: str
    content: str


@dataclass
class SentenceContext:
    token: str
    content: str
    chat_id: int | str | None = None


@dataclass
class UserState:
    persona: str = ""
    topic: str = ""
    history: list[HistoryEntry] = field(default_factory=list)
    style: ReplyStyle = "brief"
    feedback: FeedbackMode = "all"
    latest_sentence: SentenceContext | None = None


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
    def set_style(self, user_id: int, style: ReplyStyle) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_feedback(self, user_id: int, feedback: FeedbackMode) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset_history(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_turn(self, user_id: int, role: str, content: str) -> None:
        raise NotImplementedError
