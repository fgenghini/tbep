import pytest

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.llm_client_factory import LLMClientFactory


def test_create_no_provider() -> None:
    client = LLMClientFactory.create(api_key="fake")
    assert isinstance(client, ChatGPTClient)


def test_create_chatgpt_provider() -> None:
    client = LLMClientFactory.create(provider="chatgpt", api_key="fake")
    assert isinstance(client, ChatGPTClient)


def test_create_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported provider: invalid"):
        LLMClientFactory.create(provider="invalid")
