import pytest

from src.config import DEFAULT_PORT, AppConfig, ConfigError, load_config


def test_load_config_reads_required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.setenv("PORT", "9000")

    config = load_config()

    assert config == AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
    )


def test_load_config_defaults_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.delenv("PORT", raising=False)

    config = load_config()

    assert config.port == DEFAULT_PORT


def test_load_config_raises_clear_error_for_missing_required_env_var(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")

    with pytest.raises(
        ConfigError,
        match="Missing required environment variable: TELEGRAM_BOT_TOKEN",
    ):
        load_config()
