import pytest

from src.state.user_state_store import UserState, UserStateStore


def test_user_state_store_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        UserStateStore()


def test_concrete_user_state_store_can_be_instantiated() -> None:
    store = ConcreteUserStateStore()

    assert isinstance(store, UserStateStore)


def test_user_state_defaults_to_empty_values() -> None:
    state = UserState()

    assert state.persona == ""
    assert state.topic == ""
    assert state.history == []


class ConcreteUserStateStore(UserStateStore):
    def get(self, user_id: int) -> UserState:
        return UserState()

    def set_persona(self, user_id: int, persona: str) -> None:
        return None

    def set_topic(self, user_id: int, topic: str) -> None:
        return None

    def reset_history(self, user_id: int) -> None:
        return None

    def append_turn(self, user_id: int, role: str, content: str) -> None:
        return None
