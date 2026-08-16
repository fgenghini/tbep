import pytest

from src.config import AppConfig, ConfigError, load_config


def test_load_config_reads_worker_bindings() -> None:
    config = load_config(
        {
            "TELEGRAM_BOT_TOKEN": "telegram-token",
            "OPENAI_API_KEY": "openai-key",
            "WEBHOOK_SECRET_PATH": "secret-path",
            "OPENROUTER_MODEL": "model",
        }
    )
    assert config == AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        openrouter_model="model",
    )


def test_load_config_requires_selected_provider_key() -> None:
    with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
        load_config(
            {
                "TELEGRAM_BOT_TOKEN": "token",
                "WEBHOOK_SECRET_PATH": "path",
                "LLM_PROVIDER": "openrouter",
            }
        )


def test_load_config_requires_token() -> None:
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        load_config({"WEBHOOK_SECRET_PATH": "path", "OPENAI_API_KEY": "key"})
