from unittest.mock import MagicMock

import pytest

from src.commands.command_processor import CommandProcessor
from src.state.user_state_store import UserStateStore


def test_cannot_instantiate_command_processor_directly() -> None:
    store_mock = MagicMock(spec=UserStateStore)
    with pytest.raises(TypeError):
        CommandProcessor(store_mock)  # type: ignore[abstract]


def test_concrete_subclass_stores_user_state_store() -> None:
    class DummyCommandProcessor(CommandProcessor):
        def process(self, user_id: int, args: str) -> str:
            return "dummy"

    store_mock = MagicMock(spec=UserStateStore)
    processor = DummyCommandProcessor(store_mock)

    assert processor.user_state_store is store_mock
    assert processor.process(1, "args") == "dummy"
