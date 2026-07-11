from unittest.mock import MagicMock, patch

import openai
import pytest

from src.llm.chatgpt_client import ChatGPTClient, ChatGPTClientError


def test_build_request_payload() -> None:
    client = ChatGPTClient(api_key="fake-key", model="test-model")
    messages = [{"role": "user", "content": "hello"}]
    payload = client._build_request_payload(messages)

    assert payload["model"] == "test-model"
    assert payload["messages"] == messages


def test_parse_response_success() -> None:
    client = ChatGPTClient(api_key="fake-key")

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "parsed text"
    mock_response.choices = [mock_choice]

    assert client._parse_response(mock_response) == "parsed text"


def test_parse_response_empty() -> None:
    client = ChatGPTClient(api_key="fake-key")
    mock_response = MagicMock()
    mock_response.choices = []

    assert client._parse_response(mock_response) == ""


@patch("src.llm.chatgpt_client.openai.OpenAI")
def test_send_success(mock_openai_class: MagicMock) -> None:
    mock_openai_instance = MagicMock()
    mock_openai_class.return_value = mock_openai_instance

    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "success response"
    mock_response.choices = [mock_choice]

    mock_openai_instance.chat.completions.create.return_value = mock_response

    client = ChatGPTClient(api_key="fake-key", model="test-model")
    result = client.send([{"role": "user", "content": "hi"}])

    assert result == "success response"
    mock_openai_instance.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[{"role": "user", "content": "hi"}],
    )


@patch("src.llm.chatgpt_client.openai.OpenAI")
def test_send_error(mock_openai_class: MagicMock) -> None:
    mock_openai_instance = MagicMock()
    mock_openai_class.return_value = mock_openai_instance

    mock_openai_instance.chat.completions.create.side_effect = openai.APIError(
        "api error", request=MagicMock(), body=None
    )

    client = ChatGPTClient(api_key="fake-key")

    with pytest.raises(ChatGPTClientError, match="OpenAI API Error:"):
        client.send([{"role": "user", "content": "hi"}])
