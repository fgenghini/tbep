from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_LLM_PROVIDER = "chatgpt"
OPENROUTER_PROVIDER = "openrouter"
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
    llm_provider: str = DEFAULT_LLM_PROVIDER
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None


def load_config(environ: Mapping[str, str] | None = None) -> AppConfig:
    if environ is None:
        import os

        environ = os.environ
    env = environ
    llm_provider = _get_optional(env, "LLM_PROVIDER") or DEFAULT_LLM_PROVIDER
    return AppConfig(
        telegram_bot_token=_get_required(env, "TELEGRAM_BOT_TOKEN"),
        openai_api_key=_get_openai_api_key(env, llm_provider),
        webhook_secret_path=_get_required(env, "WEBHOOK_SECRET_PATH"),
        llm_provider=llm_provider,
        openrouter_api_key=_get_openrouter_api_key(env, llm_provider),
        openrouter_model=_get_optional(env, "OPENROUTER_MODEL"),
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
