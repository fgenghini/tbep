# TBEP

Telegram Bot for English Practice.

## Local Setup

Install dependencies:

```sh
uv sync
```

Run the local checks:

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Run the placeholder application entry point:

```sh
uv run python -m src.main
```
