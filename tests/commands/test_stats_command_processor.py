from unittest.mock import MagicMock

from src.commands.stats_command_processor import StatsCommandProcessor
from src.state.user_state_store import UserState, UserStateStore


def test_process_returns_persona_topic_and_message_count() -> None:
    store_mock = MagicMock(spec=UserStateStore)
    store_mock.get.return_value = UserState(
        persona="a pirate",
        topic="ships",
        history=[
            {"role": "assistant", "content": "Ahoy"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Welcome aboard"},
        ],
    )
    processor = StatsCommandProcessor(store_mock)

    result = processor.process(1, "")

    assert result == "Persona: a pirate\nTopic: ships\nMessages stored: 3"
    store_mock.get.assert_called_once_with(1)


def test_process_ignores_args() -> None:
    store_mock = MagicMock(spec=UserStateStore)
    store_mock.get.return_value = UserState(
        persona="",
        topic="",
        history=[],
    )
    processor = StatsCommandProcessor(store_mock)

    result = processor.process(123, "unexpected args")

    assert result == "Persona: \nTopic: \nMessages stored: 0"
