from unittest.mock import MagicMock

from src.commands.help_command_processor import HELP_TEXT, HelpCommandProcessor
from src.state.user_state_store import UserStateStore


def test_process_returns_help_text() -> None:
    store_mock = MagicMock(spec=UserStateStore)
    processor = HelpCommandProcessor(store_mock)

    assert processor.process(1, "") == HELP_TEXT
    assert processor.process(123, "some args") == HELP_TEXT
