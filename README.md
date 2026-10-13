# TBEP

Telegram Bot for English Practice, deployed as a Python Cloudflare Worker.

## Local development

Requires `uv >= 0.12.3` and Node.js 24 (`.node-version`), which Wrangler uses
for local development.

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
uv run python scripts/smoke_commands.py
uv run python scripts/smoke_worker.py
```

### Continuous integration

GitHub Actions runs on every pull request and on pushes to `main`:

- **Quality:** Ruff lint and formatting, strict mypy, pytest, and command smoke checks.
- **Worker runtime:** locked Wrangler/package preparation and the local Cloudflare
  Worker smoke check on Linux, using dummy credentials without Telegram or model calls.
- **Secret scanning:** Gitleaks scans PR and push commit ranges for credentials;
  a manual CI run scans the full history.
- **Python dependencies** and **npm dependencies:** audit locked packages, including
  development tools. These also run every Monday at 12:00 UTC and can be started manually.

Workflows use read-only repository permissions, pinned action commits, timeouts,
and cancel superseded runs. Python and Node versions come from `.python-version`
and `.node-version`; uv is pinned to `0.12.3`. Installs use `uv sync --locked`
and `npm ci` so stale lockfiles fail rather than being rewritten.

Configure a GitHub ruleset or branch protection for `main` to require all five
checks above before merging. Workflow files alone do not enforce merge protection.
Keep Cloudflare's production build branch set to `main`; GitHub Actions validates
changes while Cloudflare Workers Builds handles deployment. Gitleaks requires no
additional license for this personal repository; moving it to an organization
requires configuring the Gitleaks Action license.

### Smoke checks

`smoke_commands.py` sends sample Telegram updates through the Worker's `fetch`
handler in desktop Python. It checks `/help`, `/profile`, `/topic`, `/start`,
`/reset`, `/style`, and `/stats`, including state changes and `/start` defaults. The script
uses fixed model responses and captures Telegram replies in memory.

`smoke_worker.py` starts `uv run pywrangler dev --local` on an available
localhost port, sends safe HTTP requests, checks routing and input handling,
and stops the Worker. This confirms that the code starts and handles requests
in the Cloudflare runtime. Both scripts use dummy configuration and make no
Telegram or model API calls, so they need no credentials or model tokens. They
do not judge model-generated text.

Use `/style brief|balanced|detailed` to choose reply length independently of
persona. `brief` (the default) aims for one or two short sentences; `balanced`
uses a few sentences with useful context; `detailed` uses one or two short
paragraphs. These are prompt guidelines, and requests for a different level of
detail take precedence. The choice applies to subsequent replies and `/start`
openings, preserves history and other settings, and leaves corrections unchanged.
Use `/style` to see the current choice and `/stats` for all current settings.

State is in memory per warm Worker isolate. Isolate replacement can reset
persona, topic, style, and conversation history; state is not guaranteed across
isolates. No database, KV, or Durable Object is introduced here.

### Correction preferences

Use `/feedback off|important|all` to choose correction frequency (`all` by default).
`off` skips corrections; `important` focuses on material grammar or meaning errors;
`all` keeps the existing grammar and naturalness feedback. `/feedback` shows your
current mode and `/stats` includes it. Preferences survive `/start` and `/reset`
but can reset when the Worker isolate changes. Feedback stays separate from the
persona conversation.

### Alternative phrasing

Tap **Say it another way** under the latest successful conversation reply to
receive one natural alternative to your sentence, labeled **Another way:**.
This uses a separate teacher voice, works even with `/feedback off`, and does
not add a conversation turn or repeat automatic corrections. Only your latest
sentence is eligible: a new sentence, `/reset`, `/start`, or loss of Worker
state expires older buttons. Openings and error replies have no button.

If you configured Telegram's `allowed_updates` explicitly, include both
`message` and `callback_query` when registering the webhook so button taps
reach the Worker.
