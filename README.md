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

### Cloudflare Workers Builds (dashboard)

This is a single-project repository, so connect the repository in Cloudflare
and use **Settings > Build** with these exact values:

| Setting | Value |
| --- | --- |
| Root directory | `/` |
| Build command | `uv run python scripts/cloudflare_build.py` |
| Deploy command | `uv run python scripts/cloudflare_deploy.py` |
| Non-production branch deploy command | `uv run python scripts/cloudflare_preview.py` |

Leave the non-production branch command blank only when non-production branch
builds are disabled. When enabled, `versions upload` creates a preview version
without promoting it to production. Do not use the dashboard defaults
(`uv run build`, `npx wrangler deploy`, or `npx wrangler versions upload`):
there is no project build command, and Python Workers must use `pywrangler` so
their Python packages are prepared and bundled.

The build script confirms the available `uv` version, runs `npm ci` to install
the locked local Wrangler version, and runs `pywrangler sync` to vendor Python
packages for both production and preview uploads. The dashboard executes these
scripts after every connected commit; you do not run the dashboard commands
yourself.

Add this **Build variable** (not a secret) in the same dashboard section:

| Variable | Value | Why |
| --- | --- | --- |
| `SKIP_DEPENDENCY_INSTALL` | `1` | Disables Cloudflare's automatic dependency installation; the build script installs the locked dependency set instead. |

No build secret is required for this project. `.node-version` and
`.python-version` pin the Node.js and Python versions selected by the Workers
Builds image. Workers Builds currently provides `uv` in this project's build
environment (as verified by the build log); the scripts use that executable.
`package.json` and `package-lock.json` pin the local Wrangler binary that
`pywrangler` proxies to. Keep both lockfiles committed.

Runtime configuration is separate from build configuration: add
`TELEGRAM_BOT_TOKEN`, `WEBHOOK_SECRET_PATH`, `OPENAI_API_KEY` (or the selected
provider's key), and any non-secret runtime values such as `LLM_PROVIDER` in
the Worker's **Settings > Variables & Secrets**. Build variables and secrets
are only available while the dashboard build runs; they do not become Worker
runtime bindings.

References: Cloudflare documents that Workers Builds has an optional build
command, replaces the deploy command with the non-production command for
preview builds, and scopes the root directory to the build command in its
[Workers Builds configuration guide](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/).
The [build image reference](https://developers.cloudflare.com/workers/ci-cd/builds/build-image/)
documents the `.node-version`/`.python-version` overrides and
`SKIP_DEPENDENCY_INSTALL`. Cloudflare's [Python Workers guide](https://developers.cloudflare.com/workers/languages/python/)
and [package guide](https://developers.cloudflare.com/workers/languages/python/packages/)
specify `uv run pywrangler` for Python Worker development and deployment.

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
