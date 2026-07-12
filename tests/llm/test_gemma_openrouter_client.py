import json
from unittest.mock import MagicMock, patch

import pytest

from src.llm.gemma_openrouter_client import (
    OPENROUTER_CHAT_COMPLETIONS_URL,
    GemmaOpenRouterClient,
    GemmaOpenRouterClientError,
)


def test_build_request_payload_defaults_to_gemma_model_with_reasoning() -> None:
    client = GemmaOpenRouterClient(api_key="fake-key")
    messages = [{"role": "user", "content": "hello"}]

    payload = client._build_request_payload(messages)

    assert payload == {
        "model": "google/gemma-4-31b-it:free",
        "messages": messages,
        "reasoning": {"enabled": True},
    }


def test_build_request_payload_supports_model_override() -> None:
    client = GemmaOpenRouterClient(api_key="fake-key", model="custom-model")

    payload = client._build_request_payload([])

    assert payload["model"] == "custom-model"


def test_parse_response_success() -> None:
    client = GemmaOpenRouterClient(api_key="fake-key")
    response = {"choices": [{"message": {"content": "parsed text"}}]}

    assert client._parse_response(response) == "parsed text"


def test_parse_response_empty() -> None:
    client = GemmaOpenRouterClient(api_key="fake-key")

    assert client._parse_response({"choices": []}) == ""


@patch("src.llm.gemma_openrouter_client.urllib.request.urlopen")
def test_send_success(mock_urlopen: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"choices": [{"message": {"content": "success response"}}]}
    ).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = GemmaOpenRouterClient(api_key="fake-key", model="test-model")

    result = client.send([{"role": "user", "content": "hi"}])

    assert result == "success response"
    request = mock_urlopen.call_args.args[0]
    assert request.full_url == OPENROUTER_CHAT_COMPLETIONS_URL
    assert request.headers["Authorization"] == "Bearer fake-key"
    assert json.loads(request.data.decode("utf-8")) == {
        "model": "test-model",
        "messages": [{"role": "user", "content": "hi"}],
        "reasoning": {"enabled": True},
    }


@patch("src.llm.gemma_openrouter_client.urllib.request.urlopen")
def test_send_error(mock_urlopen: MagicMock) -> None:
    mock_urlopen.side_effect = ValueError("bad response")
    client = GemmaOpenRouterClient(api_key="fake-key")

    with pytest.raises(GemmaOpenRouterClientError, match="OpenRouter API Error:"):
        client.send([{"role": "user", "content": "hi"}])
