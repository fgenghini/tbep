from src.state.user_state_store import UserState, UserStateStore


class UserStateStoreMemory(UserStateStore):
    def __init__(self) -> None:
        self._store: dict[int, UserState] = {}

    def get(self, user_id: int) -> UserState:
        if user_id not in self._store:
            self._store[user_id] = UserState()
        return self._store[user_id]

    def set_persona(self, user_id: int, persona: str) -> None:
        state = self.get(user_id)
        state.persona = persona

    def set_topic(self, user_id: int, topic: str) -> None:
        state = self.get(user_id)
        state.topic = topic

    def reset_history(self, user_id: int) -> None:
        state = self.get(user_id)
        state.history = []

    def append_turn(self, user_id: int, role: str, content: str) -> None:
        state = self.get(user_id)
        state.history.append({"role": role, "content": content})
