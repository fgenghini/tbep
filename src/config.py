from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_PORT = 8000
DEFAULT_LLM_PROVIDER = "chatgpt"
OPENROUTER_PROVIDER = "gemma-openrouter"
REQUIRED_ENV_VARS = (
    "TELEGRAM_BOT_TOKEN",
    "WEBHOOK_SECRET_PATH",
)


class ConfigError(RuntimeError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    telegram_bot_token: str
    openai_api_key: str | None
    webhook_secret_path: str
    port: int = DEFAULT_PORT
    webhook_base_url: str | None = None
    llm_provider: str = DEFAULT_LLM_PROVIDER
    openrouter_api_key: str | None = None

    @property
    def webhook_url(self) -> str | None:
        if self.webhook_base_url is None:
            return None
        return f"{self.webhook_base_url}/{self.webhook_secret_path}"


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    env = os.environ if environ is None else environ
    llm_provider = _get_optional(env, "LLM_PROVIDER") or DEFAULT_LLM_PROVIDER
    return AppConfig(
        telegram_bot_token=_get_required(env, "TELEGRAM_BOT_TOKEN"),
        openai_api_key=_get_openai_api_key(env, llm_provider),
        webhook_secret_path=_get_required(env, "WEBHOOK_SECRET_PATH"),
        port=_get_port(env),
        webhook_base_url=_get_optional(env, "WEBHOOK_BASE_URL"),
        llm_provider=llm_provider,
        openrouter_api_key=_get_openrouter_api_key(env, llm_provider),
    )


def _get_openai_api_key(
    environ: Mapping[str, str],
    llm_provider: str,
) -> str | None:
    if llm_provider == OPENROUTER_PROVIDER:
        return _get_optional(environ, "OPENAI_API_KEY")
    return _get_required(environ, "OPENAI_API_KEY")


def _get_openrouter_api_key(
    environ: Mapping[str, str],
    llm_provider: str,
) -> str | None:
    if llm_provider == OPENROUTER_PROVIDER:
        return _get_required(environ, "OPENROUTER_API_KEY")
    return _get_optional(environ, "OPENROUTER_API_KEY")


def _get_required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if value is None or value.strip() == "":
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def _get_optional(environ: Mapping[str, str], name: str) -> str | None:
    value = environ.get(name)
    if value is None or value.strip() == "":
        return None
    return value


def _get_port(environ: Mapping[str, str]) -> int:
    raw_port = environ.get("PORT")
    if raw_port is None or raw_port.strip() == "":
        return DEFAULT_PORT

    try:
        return int(raw_port)
    except ValueError as error:
        raise ConfigError("PORT must be an integer") from error
