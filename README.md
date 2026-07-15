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

Run the bot:

```sh
uv run python -m src.main
```

The bot uses Telegram webhooks, so local runs need a public HTTPS URL that can
forward Telegram requests to your machine.

## Configuration

Set these environment variables before running the bot:

| Variable | Required | Description |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from BotFather. |
| `LLM_PROVIDER` | No | LLM provider. Defaults to `chatgpt`; set to `openrouter` to use OpenRouter. |
| `OPENAI_API_KEY` | For `chatgpt` | API key used by the ChatGPT client. |
| `OPENROUTER_API_KEY` | For `openrouter` | API key used by the OpenRouter client. |
| `OPENROUTER_MODEL` | No | OpenRouter model name. Defaults to `google/gemma-4-31b-it:free`. |
| `WEBHOOK_SECRET_PATH` | Yes | Secret URL path Telegram will call for webhook updates. |
| `WEBHOOK_BASE_URL` | Yes | Public HTTPS base URL for the deployed app. The bot registers `WEBHOOK_BASE_URL/WEBHOOK_SECRET_PATH` with Telegram. |
| `PORT` | No | HTTP port for the webhook server. Defaults to `8000`; Railway provides this automatically. |

## Railway Deployment

1. Create or link a Railway project for this repository.
2. Configure the project to deploy from the branch you want to run.
3. Add the required environment variables in Railway:
   `TELEGRAM_BOT_TOKEN`, `WEBHOOK_SECRET_PATH`, `WEBHOOK_BASE_URL`, and the
   API key for your selected `LLM_PROVIDER`.
4. Set `WEBHOOK_BASE_URL` to the public Railway app URL, for example
   `https://your-service.up.railway.app`.
5. Deploy the service. Railway supplies `PORT`; do not set it manually unless
   you have a specific reason.
6. Confirm startup succeeds in the Railway logs. On startup, the bot calls
   Telegram through `Application.run_webhook(...)` and registers the webhook URL.

The `Procfile` starts the application with:

```sh
web: uv run python -m src.main
```

Railway's free tier may sleep when idle. Because TBEP v1 stores user state only
in process memory, sleeping, restarts, or redeploys clear conversation history
and reset in-memory persona/topic state.
