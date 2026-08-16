# TBEP

Telegram Bot for English Practice, deployed as a Python Cloudflare Worker.

## Local development

Requires `uv >= 0.12.3` and Node.js (Wrangler's local CLI prerequisite).

```sh
uv sync
cp .dev.vars.example .dev.vars
# edit .dev.vars with local credentials
uv run pywrangler dev
```

The Worker accepts Telegram updates at `/<WEBHOOK_SECRET_PATH>`, dispatches
commands or plain text, and calls Telegram asynchronously. It does not bind a
port or register a webhook during startup.

## Configuration and deployment

`TELEGRAM_BOT_TOKEN`, `WEBHOOK_SECRET_PATH`, and the selected provider's API
key are required. `LLM_PROVIDER` defaults to `chatgpt`; `OPENROUTER_MODEL` is
optional. Bindings are read from the Worker environment.

```sh
uv run pywrangler secret put TELEGRAM_BOT_TOKEN
uv run pywrangler secret put WEBHOOK_SECRET_PATH
uv run pywrangler secret put OPENAI_API_KEY
uv run pywrangler deploy
uv run pywrangler tail
```

Deploy the new Worker first without changing the old webhook. Then call
Telegram `setWebhook` with the deployed Worker URL plus the secret path and
verify it with `getWebhookInfo`. Retire the old deployment only after that
verification, so both runtimes never process updates simultaneously. Roll
back with `uv run pywrangler rollback` if needed.

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

State is in memory per warm Worker isolate. Isolate replacement can reset
persona, topic, and conversation history; state is not guaranteed across
isolates. No database, KV, or Durable Object is introduced here.
