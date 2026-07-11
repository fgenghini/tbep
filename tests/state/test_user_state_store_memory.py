from src.state.user_state_store import UserState
from src.state.user_state_store_memory import UserStateStoreMemory


def test_get_new_user_returns_default() -> None:
    store = UserStateStoreMemory()
    state = store.get(1)
    assert isinstance(state, UserState)
    assert state.persona == ""
    assert state.topic == ""
    assert state.history == []


def test_set_persona_and_topic_persists() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")

    state = store.get(1)
    assert state.persona == "pirate"
    assert state.topic == "ships"


def test_reset_history_clears_only_history() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "pirate")
    store.set_topic(1, "ships")
    store.append_turn(1, "user", "hello")
    store.append_turn(1, "bot", "ahoy")

    store.reset_history(1)

    state = store.get(1)
    assert state.persona == "pirate"
    assert state.topic == "ships"
    assert state.history == []


def test_append_turn_adds_in_order() -> None:
    store = UserStateStoreMemory()
    store.append_turn(1, "user", "hello")
    store.append_turn(1, "bot", "hi")

    state = store.get(1)
    assert len(state.history) == 2
    assert state.history[0] == {"role": "user", "content": "hello"}
    assert state.history[1] == {"role": "bot", "content": "hi"}


def test_isolation_per_user() -> None:
    store = UserStateStoreMemory()
    store.set_persona(1, "user1_persona")
    store.set_persona(2, "user2_persona")
    store.append_turn(1, "user", "hello 1")
    store.append_turn(2, "user", "hello 2")

    state1 = store.get(1)
    state2 = store.get(2)

    assert state1.persona == "user1_persona"
    assert state2.persona == "user2_persona"
    assert len(state1.history) == 1
    assert state1.history[0]["content"] == "hello 1"
    assert len(state2.history) == 1
    assert state2.history[0]["content"] == "hello 2"
