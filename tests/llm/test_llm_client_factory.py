import pytest

from src.llm.chatgpt_client import ChatGPTClient
from src.llm.llm_client_factory import (
    CHATGPT_PROVIDER,
    OPENROUTER_PROVIDER,
    PROVIDER_ENV_VAR,
    LLMClientFactory,
)
from src.llm.openrouter_client import OpenRouterClient


def test_create_defaults_to_chatgpt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PROVIDER_ENV_VAR, raising=False)

    client = LLMClientFactory(api_key="fake").create()

    assert isinstance(client, ChatGPTClient)


def test_create_uses_provider_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV_VAR, CHATGPT_PROVIDER)

    client = LLMClientFactory(api_key="fake").create()

    assert isinstance(client, ChatGPTClient)


def test_create_supports_openrouter_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PROVIDER_ENV_VAR, OPENROUTER_PROVIDER)

    client = LLMClientFactory(openrouter_api_key="fake-openrouter-key").create()

    assert isinstance(client, OpenRouterClient)
    assert client.api_key == "fake-openrouter-key"


def test_create_supports_provider_from_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PROVIDER_ENV_VAR, raising=False)

    client = LLMClientFactory(
        provider=OPENROUTER_PROVIDER,
        openrouter_api_key="fake-openrouter-key",
    ).create()

    assert isinstance(client, OpenRouterClient)


def test_create_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(PROVIDER_ENV_VAR, "invalid")

    with pytest.raises(ValueError, match="Unsupported provider: invalid"):
        LLMClientFactory().create()
