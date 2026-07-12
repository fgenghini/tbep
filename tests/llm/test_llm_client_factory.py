import pytest

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.llm_client_factory import PROVIDER_ENV_VAR, LLMClientFactory


def test_create_defaults_to_chatgpt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PROVIDER_ENV_VAR, raising=False)

    client = LLMClientFactory(api_key="fake").create()

    assert isinstance(client, ChatGPTClient)


def test_create_uses_provider_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV_VAR, "chatgpt")

    client = LLMClientFactory(api_key="fake").create()

    assert isinstance(client, ChatGPTClient)


def test_create_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV_VAR, "invalid")

    with pytest.raises(ValueError, match="Unsupported provider: invalid"):
        LLMClientFactory().create()
