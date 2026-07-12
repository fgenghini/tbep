from unittest.mock import MagicMock

import pytest

from src.messages.message_processor import MessageProcessor
from src.state.user_state_store import UserStateStore


def test_cannot_instantiate_message_processor_directly() -> None:
    store_mock = MagicMock(spec=UserStateStore)
    factory_mock = MagicMock()
    with pytest.raises(TypeError):
        MessageProcessor(store_mock, factory_mock)  # type: ignore[abstract]


def test_constructor_calls_factory() -> None:
    class DummyMessageProcessor(MessageProcessor):
        def process(self, user_id: int, content: str) -> dict[str, str | None]:
            return {}

    store_mock = MagicMock(spec=UserStateStore)
    factory_mock = MagicMock()
    llm_mock = MagicMock()
    factory_mock.create.return_value = llm_mock

    processor = DummyMessageProcessor(store_mock, factory_mock)

    factory_mock.create.assert_called_once_with()
    assert processor.user_state_store is store_mock
    assert processor.llm_client is llm_mock
