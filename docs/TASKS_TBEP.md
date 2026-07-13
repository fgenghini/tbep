# Implementation Tasks: TBEP (Telegram Bot for English Practice)

This document breaks down the implementation of TBEP (per `ARCH_TBEP.md`) into small, incremental tasks, starting from an empty GitHub repository. Tasks are ordered by dependency — each task lists what must be completed before it can start.

## How to Use This Document

- Work through tasks in dependency order (a task's "Depends on" list must be done first). Tasks with no shared dependency chain between them can be done in any order relative to each other.
- **Every task that adds/changes code must include unit tests** for that code, placed in the mirrored `tests/` path (per `ARCH_TBEP.md` Section 4).
- **Every task ends with a PR**, and a PR must only be opened after, locally:
  1. `uv run ruff check .` passes with no errors.
  2. `uv run ruff format --check .` passes with no formatting issues (or `uv run ruff format .` has been run and changes committed).
  3. `uv run mypy src` passes with no errors.
  4. `uv run pytest` passes with all tests green.
- If any of the above fail, fix the issue before opening the PR — do not open a PR with failing checks.
- Each task should be its own branch and its own PR (small, reviewable increments) — do not bundle multiple tasks into one PR.
- **Tracking progress:** this file lives at `docs/TASKS_TBEP.md` in the repo, alongside `docs/PRD_TBEP.md` and `docs/ARCH_TBEP.md`. Each task below has a `Status` line. When a PR for a task is opened, update that task's `Status` to `Done` as part of the same PR (i.e., the PR that implements the task also includes the edit to this file marking it done), so `docs/TASKS_TBEP.md` always reflects what's actually been shipped/in review versus what's left.

---

## Dependency Overview

```
TASK-01 (Repo bootstrap & tooling)
   │
   ├── TASK-02 (Config loading)
   │
   ├── TASK-03 (UserStateStore base + UserState model)
   │      │
   │      └── TASK-04 (UserStateStoreMemory)
   │
   ├── TASK-05 (LLMClient base)
   │      │
   │      └── TASK-06 (ChatGPTClient)  ← also depends on TASK-02
   │             │
   │             └── TASK-07 (LLMClientFactory)
   │
   └── TASK-10 (CommandProcessor base)  ← also depends on TASK-03

TASK-07 + TASK-04 → TASK-08 (MessageProcessor base)
TASK-08 → TASK-09 (TextMessageProcessor)

TASK-10 → TASK-11 (HelpCommandProcessor)
TASK-10 + TASK-09 → TASK-12 (ResetCommandProcessor)
TASK-10 + TASK-09 → TASK-13 (ProfileCommandProcessor)
TASK-10 + TASK-09 → TASK-14 (TopicCommandProcessor)
TASK-10 + TASK-09 → TASK-15 (StartCommandProcessor)

TASK-11 + TASK-12 + TASK-13 + TASK-14 + TASK-15 + TASK-02 → TASK-16 (main.py wiring + webhook)
TASK-16 → TASK-17 (Railway deployment config)
```

---

## TASK-01: Repository Bootstrap & Tooling

**Depends on:** none (first task, starting from empty repo).

**Status:** [x] Done

**Goal:** Set up the project skeleton and developer tooling so every subsequent task can build/lint/type-check/test from day one.

**Scope:**
- Initialize `pyproject.toml` via `uv init` (or equivalent), declaring project metadata.
- Add `python-telegram-bot` and `openai` (or the relevant ChatGPT SDK) as dependencies via `uv add`.
- Add `ruff`, `mypy`, `pytest` as dev dependencies via `uv add --dev`.
- Configure `[tool.ruff]` (lint + format rules) in `pyproject.toml`.
- Configure `[tool.mypy]` (strictness level, `src` as the checked path) in `pyproject.toml`.
- Configure `[tool.pytest.ini_options]` with `testpaths = ["tests"]`.
- Create the empty folder skeleton per `ARCH_TBEP.md` Section 4: `src/` (with `state/`, `commands/`, `messages/`, `llm/` subfolders and empty `__init__.py` files as needed) and mirrored `tests/` subfolders.
- Add a placeholder `src/main.py` (e.g., a `def main(): pass` stub) so the project is importable/runnable at a trivial level.
- Add `.gitignore` (Python/uv-appropriate: `.venv`, `__pycache__`, `.mypy_cache`, `.ruff_cache`, `.env`, etc.).
- Add a placeholder `Procfile` (finalized in TASK-17).
- Add a minimal `README.md` with project name and a "how to set up locally" section (`uv sync`, `uv run pytest`, etc.).
- Create a `docs/` folder at the repo root and add `docs/PRD_TBEP.md`, `docs/ARCH_TBEP.md`, and `docs/TASKS_TBEP.md` (this file) — these are the project's living reference documents going forward.

**Unit tests:** None yet (no logic exists). Add a trivial smoke test (e.g., `tests/test_smoke.py` asserting `1 + 1 == 2` or that `src.main` imports cleanly) to confirm `pytest` and the test path config work end-to-end.

**PR gate:** `ruff check .`, `ruff format --check .`, `mypy src`, `pytest` all pass (trivially, given the smoke test).

---

## TASK-02: Configuration Loading (`config.py`)

**Depends on:** TASK-01.

**Status:** [x] Done

**Goal:** Centralize environment variable loading so other components (LLM client, main.py) can read config consistently.

**Scope:**
- Implement `src/config.py` exposing a way to read: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `WEBHOOK_SECRET_PATH`, `PORT` (with a sensible local default for `PORT`, e.g. `8000`).
- Fail fast (clear error) if a required variable is missing, rather than silently proceeding.

**Unit tests:**
- Test that all required env vars are read correctly when set (using monkeypatched/mocked env).
- Test that a missing required env var raises a clear error.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-03: `UserStateStore` Base Class & `UserState` Model

**Depends on:** TASK-01.

**Status:** [x] Done

**Goal:** Define the storage interface and the data model it operates on, per `ARCH_TBEP.md` Section 5.5.

**Scope:**
- Implement `UserState` (persona: str, topic: str, history: list of role/content entries).
- Implement `UserStateStore` as an abstract base class with abstract methods: `get`, `set_persona`, `set_topic`, `reset_history`, `append_turn`.

**Unit tests:**
- Test that `UserStateStore` cannot be instantiated directly (raises `TypeError` since it's abstract).
- Test that a minimal concrete subclass implementing all abstract methods can be instantiated (confirms the ABC contract is well-formed).

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-04: `UserStateStoreMemory` Implementation

**Depends on:** TASK-03.

**Status:** [x] Done

**Goal:** Provide the in-memory implementation used in v1.

**Scope:**
- Implement `UserStateStoreMemory(UserStateStore)` backed by an in-memory dict keyed by `user_id`.
- Ensure `get()` for an unseen `user_id` returns a sensible default `UserState` (e.g., empty persona/topic/history) rather than raising.

**Unit tests:**
- `get()` for a new user returns a default/empty state.
- `set_persona()` / `set_topic()` persist and are retrievable via `get()`.
- `reset_history()` clears `history` but leaves `persona`/`topic` untouched.
- `append_turn()` adds entries to `history` in order.
- State is correctly isolated per `user_id` (two different users don't leak into each other's state).

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-05: `LLMClient` Base Class

**Depends on:** TASK-01.

**Status:** [x] Done

**Goal:** Define the LLM integration interface, per `ARCH_TBEP.md` Section 5.3.

**Scope:**
- Implement `LLMClient` as an abstract base class with `__init__(self, api_key, model=None, **config)` and an abstract `send(self, messages: list) -> str`.

**Unit tests:**
- Test that `LLMClient` cannot be instantiated directly.
- Test that a minimal concrete subclass can be instantiated and stores `api_key`/`model`/`config` correctly.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-06: `ChatGPTClient` Implementation

**Depends on:** TASK-05, TASK-02 (for API key config pattern).

**Status:** [x] Done

**Goal:** Implement the concrete ChatGPT-backed LLM client.

**Scope:**
- Implement `ChatGPTClient(LLMClient)`, implementing `send()` against the OpenAI ChatGPT API.
- Per the coding guidelines in `ARCH_TBEP.md` Section 12, split `send()` into small helpers: e.g. `_build_request_payload()`, `_call_api()`, `_parse_response()`.
- Handle and surface API errors in a way `TextMessageProcessor` (TASK-09) can catch and map to the fallback message.

**Unit tests:**
- `_build_request_payload()` produces the expected structure from given `messages`.
- `_parse_response()` correctly extracts text from a mocked API response object.
- `send()` end-to-end with the actual OpenAI API call mocked (no real network calls in tests), covering both a success case and an error/timeout case (verifying the error propagates in a way callers can handle).

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-07: `LLMClientFactory`

**Depends on:** TASK-05, TASK-06.

**Status:** [x] Done

**Goal:** Implement the factory that resolves an `LLMClient` implementation by provider name, per `ARCH_TBEP.md` Section 5.4.

**Scope:**
- Implement `LLMClientFactory.create(provider="chatgpt", **config)`, defaulting to `ChatGPTClient` and raising `ValueError` for unsupported providers.

**Unit tests:**
- `create()` with no provider argument returns a `ChatGPTClient` instance.
- `create()` with `provider="chatgpt"` explicitly returns a `ChatGPTClient` instance.
- `create()` with an unsupported provider raises `ValueError`.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-08: `MessageProcessor` Base Class

**Depends on:** TASK-04, TASK-07.

**Status:** [x] Done

**Goal:** Define the message-handling interface, per `ARCH_TBEP.md` Section 5.2.

**Scope:**
- Implement `MessageProcessor` as an abstract base class whose `__init__(self, user_state_store, llm_client_factory, **llm_config)` calls `llm_client_factory.create(**llm_config)` once and stores the result as `self.llm_client`.
- Declare abstract `process(self, user_id: int, content) -> dict`.

**Unit tests:**
- Test that the constructor calls `llm_client_factory.create()` exactly once with the expected config, using a mocked factory, and that `self.llm_client` holds the returned mock.
- Test that `MessageProcessor` cannot be instantiated directly (abstract).

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-09: `TextMessageProcessor` Implementation

**Depends on:** TASK-08.

**Status:** [x] Done

**Goal:** Implement the v1 message processor that drives persona replies and corrections.

**Scope:**
- Implement `TextMessageProcessor(MessageProcessor)`.
- Per the coding guidelines, split `process()` into small helpers, e.g.: `_build_persona_prompt()`, `_generate_persona_reply()`, `_generate_correction()`, `_update_history()`.
- On any LLM error (from `self.llm_client.send()`), return the fixed fallback response ("An error occurred. Try again in a moment.") with no correction, per `ARCH_TBEP.md` Section 9.
- When no correction is needed, ensure the returned dict reflects that (`correction: None`) so callers send nothing for it (per PRD Section 5.3).

**Unit tests:**
- `process()` returns both a persona reply and a correction when the (mocked) LLM indicates an error was found.
- `process()` returns a persona reply with `correction: None` when the (mocked) LLM indicates no error.
- `process()` updates the user's history via `UserStateStore` after a successful turn (using a mocked/real `UserStateStoreMemory`).
- `process()` returns the fixed fallback message and no correction when `llm_client.send()` raises.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-10: `CommandProcessor` Base Class

**Depends on:** TASK-03.

**Status:** [x] Done

**Goal:** Define the command-handling interface, per `ARCH_TBEP.md` Section 5.1.

**Scope:**
- Implement `CommandProcessor` as an abstract base class with `__init__(self, user_state_store)` and abstract `process(self, user_id: int, args: str) -> str`.

**Unit tests:**
- Test that `CommandProcessor` cannot be instantiated directly.
- Test that a minimal concrete subclass can be instantiated and stores `user_state_store` correctly.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-11: `HelpCommandProcessor`

**Depends on:** TASK-10.

**Status:** [x] Done

**Goal:** Implement the simplest command (no LLM/state interaction) to validate the command pattern end-to-end.

**Scope:**
- Implement `HelpCommandProcessor(CommandProcessor)` returning static help text describing all commands and how corrections work (content can be a simple constant string for now).

**Unit tests:**
- `process()` returns the expected static help text regardless of `args`/`user_id`.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-12: `ResetCommandProcessor`

**Depends on:** TASK-10, TASK-09.

**Status:** [x] Done

**Goal:** Implement `/reset` — clears history without starting a conversation.

**Scope:**
- Implement `ResetCommandProcessor(CommandProcessor)`, using `UserStateStore.reset_history()` and returning a confirmation that directs the user to `/start`.

**Unit tests:**
- `process()` calls `reset_history()` on the (mocked) `UserStateStore`.
- `process()` does not call the LLM or append an opening message.
- Persona/topic are left unchanged after `process()`.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-13: `ProfileCommandProcessor`

**Depends on:** TASK-10, TASK-09.

**Status:** [x] Done

**Goal:** Implement `/profile` — sets the persona without starting a conversation.

**Scope:**
- Implement `ProfileCommandProcessor(CommandProcessor)`: sets persona from `args` via `UserStateStore.set_persona()` and returns a confirmation that directs the user to `/start`.

**Unit tests:**
- `process()` sets the persona from `args` on the (mocked) `UserStateStore`.
- `process()` leaves topic and history unchanged.
- `process()` does not call the LLM or append an opening message.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-14: `TopicCommandProcessor`

**Depends on:** TASK-10, TASK-09.

**Status:** [x] Done

**Goal:** Implement `/topic` — sets the topic without starting a conversation.

**Scope:**
- Implement `TopicCommandProcessor(CommandProcessor)`: sets topic from `args` and returns a confirmation that directs the user to `/start`.

**Unit tests:**
- `process()` sets the topic from `args` on the (mocked) `UserStateStore`.
- `process()` leaves persona and history unchanged.
- `process()` does not call the LLM or append an opening message.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-15: `StartCommandProcessor`

**Depends on:** TASK-10, TASK-09.

**Status:** [x] Done

**Goal:** Implement `/start` — applies defaults if unset, resets conversation, starts it, and mentions `/help`.

**Scope:**
- Implement `StartCommandProcessor(CommandProcessor)`: applies default persona/topic if not already set (without overwriting existing customization), resets history, generates an opening message, and includes a short mention that `/help` is available (per PRD decision — no full inline explanation).

**Unit tests:**
- `process()` applies both defaults for a brand-new user.
- `process()` does *not* override an existing persona/topic for a returning user who already customized them.
- `process()` resets history and returns an in-character opening message referencing `/help`.

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-16: `main.py` Wiring & Webhook Setup

**Depends on:** TASK-02, TASK-11, TASK-12, TASK-13, TASK-14, TASK-15.

**Status:** [x] Done

**Goal:** Wire all components together into a running webhook-based bot, per `ARCH_TBEP.md` Sections 7–8.

**Scope:**
- Implement `src/main.py`: load config, construct `UserStateStoreMemory`, `LLMClientFactory`, and the `TextMessageProcessor`/`CommandProcessor` instances.
- Register `CommandHandler`s for `/start`, `/profile`, `/topic`, `/help`, `/reset`, and a `MessageHandler` for plain text.
- Each handler is a thin adapter that extracts `user_id`/`args`/`content` from the `Update`, calls the relevant processor, and sends the persona reply and correction as two separate messages (per PRD Section 5.3).
- Start the app via `Application.run_webhook(...)`, binding to `PORT`, and register the webhook URL with Telegram using `WEBHOOK_SECRET_PATH`.
- Register a global error handler (`Application.add_error_handler`) that logs unhandled exceptions.

**Unit tests:**
- Test each handler adapter function in isolation (mocking the Telegram `Update`/`Context` and the relevant processor) to confirm it extracts the right arguments, calls `process()` correctly, and sends the expected message(s) — including the two-message split for persona reply + correction.
- Test that the global error handler logs (doesn't crash) on a simulated unhandled exception.
- Webhook startup/registration itself is more of an integration concern; a full end-to-end webhook test is not required here, but a unit test can confirm the app builds its handler registrations correctly (e.g., inspecting the `Application`'s registered handlers).

**PR gate:** ruff, mypy, pytest all pass.

---

## TASK-17: Railway Deployment Configuration

**Depends on:** TASK-16.

**Status:** [x] Done

**Goal:** Finalize deployment configuration so the bot can run on Railway's free tier.

**Scope:**
- Finalize the `Procfile` to run `src/main.py` correctly under `uv run`.
- Document required environment variables (`TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `WEBHOOK_SECRET_PATH`) in `README.md`, plus how Railway provides `PORT`.
- Document the deployment steps (linking the Railway project, setting env vars, first deploy, confirming the webhook registers successfully) in `README.md`.
- Note the free-tier sleep/in-memory-state tradeoff (per `ARCH_TBEP.md` Section 8) in `README.md` so it's not a surprise in production.

**Unit tests:** None required (this task is configuration/documentation, not application code). If any small config-parsing logic is added as part of this task, it should still get unit tests per the general rule.

**PR gate:** ruff, mypy, pytest all pass (unchanged from TASK-16, confirming this task didn't break anything).

---

## Notes for Whoever Executes These Tasks

- Tasks 03/05/10 (the three abstract base classes) and TASK-01/02 have no dependency on each other and can be done in parallel/in any order once TASK-01 is complete.
- Tasks 11–15 (the five command processors) all depend on the same two things (TASK-10 and TASK-09) and can similarly be done in any order relative to each other.
- Resist the urge to combine small tasks into a single PR "for efficiency" — the point of this breakdown is small, easily-reviewable increments, each independently green on lint/type-check/tests.
