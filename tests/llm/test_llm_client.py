import pytest

from src.llm.llm_client import LLMClient


def test_cannot_instantiate_llm_client_directly() -> None:
    with pytest.raises(TypeError):
        LLMClient("fake-key")  # type: ignore[abstract]


def test_concrete_subclass_stores_args() -> None:
    class DummyClient(LLMClient):
        def send(self, messages: list[dict[str, str]]) -> str:
            return "response"

    client = DummyClient("my-api-key", model="my-model", timeout=10, retries=3)

    assert client.api_key == "my-api-key"
    assert client.model == "my-model"
    assert client.config == {"timeout": 10, "retries": 3}
    assert client.send([]) == "response"
