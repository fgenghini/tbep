import pytest

from src.config import DEFAULT_PORT, AppConfig, ConfigError, load_config


def test_load_config_reads_required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("WEBHOOK_BASE_URL", "https://example.com")

    config = load_config()

    assert config == AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        port=9000,
        webhook_base_url="https://example.com",
        openrouter_api_key="openrouter-key",
    )


def test_load_config_defaults_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.delenv("PORT", raising=False)

    config = load_config()

    assert config.port == DEFAULT_PORT


def test_config_builds_webhook_url_when_base_url_is_set() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
        webhook_base_url="https://example.com",
    )

    assert config.webhook_url == "https://example.com/secret-path"


def test_config_webhook_url_is_none_without_base_url() -> None:
    config = AppConfig(
        telegram_bot_token="telegram-token",
        openai_api_key="openai-key",
        webhook_secret_path="secret-path",
    )

    assert config.webhook_url is None


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


def test_load_config_uses_openrouter_key_for_openrouter_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")

    config = load_config()

    assert config.llm_provider == "openrouter"
    assert config.openai_api_key is None
    assert config.openrouter_api_key == "openrouter-key"


def test_load_config_requires_openrouter_key_for_openrouter_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("WEBHOOK_SECRET_PATH", "secret-path")
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(
        ConfigError,
        match="Missing required environment variable: OPENROUTER_API_KEY",
    ):
        load_config()
