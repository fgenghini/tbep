import asyncio
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from main import Default


def message(text="I like coffee.", user_id=123, chat_id=123):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1,
            "from": {"id": user_id, "is_bot": False, "first_name": "Learner"},
            "chat": {"id": chat_id, "type": "private"},
            "text": text,
        },
    }


def callback(data, user_id=123, chat_id=123):
    return {
        "update_id": 2,
        "callback_query": {
            "id": "tap-1",
            "from": {"id": user_id, "is_bot": False, "first_name": "Learner"},
            "chat_instance": "instance",
            "data": data,
            "message": {
                "message_id": 20,
                "date": 1,
                "from": {"id": 999, "is_bot": True, "first_name": "TBEP"},
                "chat": {"id": chat_id, "type": "private"},
                "text": "Nice!",
            },
        },
    }


async def deliver(worker, update):
    request = SimpleNamespace(
        url="https://tbep.example/secret",
        method="POST",
        text=AsyncMock(return_value=json.dumps(update)),
    )
    return await worker.fetch(request)


@pytest.fixture
def setup(monkeypatch):
    posts = []

    def transport(request):
        payload = json.loads(request.content)
        posts.append((request.url.path.rsplit("/", 1)[-1], payload))
        return httpx.Response(200, json={"ok": True, "result": True})

    client_type = httpx.AsyncClient
    monkeypatch.setattr(
        "main.httpx.AsyncClient",
        lambda **kwargs: client_type(
            transport=httpx.MockTransport(transport), **kwargs
        ),
    )
    llm = MagicMock()
    llm.send = AsyncMock(side_effect=["Nice!", "NO_CORRECTION", "I enjoy coffee."])
    monkeypatch.setattr(
        "llm.llm_client_factory.LLMClientFactory.create", lambda self: llm
    )
    worker = Default()
    worker.env = SimpleNamespace(
        TELEGRAM_BOT_TOKEN="token",
        OPENAI_API_KEY="key",
        WEBHOOK_SECRET_PATH="secret",
        LLM_PROVIDER="chatgpt",
    )
    return worker, llm, posts


def button_data(posts):
    payload = next(payload for method, payload in posts if method == "sendMessage")
    button = payload["reply_markup"]["inline_keyboard"][0][0]
    assert button["text"] == "Say it another way"
    assert 1 <= len(button["callback_data"].encode()) <= 64
    assert "coffee" not in button["callback_data"]
    return button["callback_data"]


def test_button_callback_rephrases_without_changing_conversation(setup):
    worker, llm, posts = setup

    async def run():
        assert (await deliver(worker, message())).status == 200
        data = button_data(posts)
        store = worker.components.text.user_state_store
        before = deepcopy(store.get(123))
        posts.clear()

        async def alternative(messages):
            assert posts == [("answerCallbackQuery", {"callback_query_id": "tap-1"})]
            assert messages[1] == {"role": "user", "content": "I like coffee."}
            prompt = messages[0]["content"].lower()
            assert "one" in prompt and "meaning" in prompt and "teacher" in prompt
            return "I enjoy coffee."

        llm.send.side_effect = alternative
        assert (await deliver(worker, callback(data))).status == 200
        assert posts[-1] == (
            "sendMessage",
            {"chat_id": 123, "text": "Another way: I enjoy coffee."},
        )
        assert store.get(123) == before

    asyncio.run(run())


@pytest.mark.parametrize(
    "reason",
    [
        "new sentence",
        "failed sentence",
        "reset",
        "start",
        "restart",
        "other user",
        "other chat",
        "wrong token",
    ],
)
def test_stale_or_unowned_button_never_calls_model(setup, reason):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message())
        data = button_data(posts)
        tap = callback(data)
        if reason in ("new sentence", "failed sentence"):
            llm.send.side_effect = (
                ["New reply", "NO_CORRECTION"]
                if reason == "new sentence"
                else RuntimeError("Unavailable")
            )
            await deliver(worker, message("A newer sentence."))
        elif reason in ("reset", "start"):
            llm.send.side_effect = None
            llm.send.return_value = "Hello!"
            await deliver(worker, message("/" + reason))
        elif reason == "restart":
            worker.components = None
        elif reason == "other user":
            tap = callback(data, user_id=456)
        elif reason == "other chat":
            tap = callback(data, chat_id=456)
        else:
            tap = callback("rephrase:wrong")
        llm.send.reset_mock()
        posts.clear()
        assert (await deliver(worker, tap)).status == 200
        llm.send.assert_not_awaited()
        assert posts[0][0] == "answerCallbackQuery"
        assert "no longer available" in str(posts)
        assert "I like coffee" not in str(posts)

    asyncio.run(run())


def test_feedback_off_still_allows_button_and_no_duplicate_correction(setup):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message("/feedback off"))
        posts.clear()
        llm.send.side_effect = ["Nice!", "I enjoy coffee."]
        await deliver(worker, message())
        data = button_data(posts)
        assert len(posts) == 1
        posts.clear()
        await deliver(worker, callback(data))
        assert len([p for m, p in posts if m == "sendMessage"]) == 1
        assert llm.send.await_count == 2

    asyncio.run(run())


@pytest.mark.parametrize("output", [RuntimeError("Model unavailable"), "  "])
def test_rephrase_failure_returns_fallback(setup, output):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message())
        data = button_data(posts)
        llm.send.side_effect = output if isinstance(output, Exception) else None
        llm.send.return_value = output
        posts.clear()
        assert (await deliver(worker, callback(data))).status == 200
        assert posts[0][0] == "answerCallbackQuery"
        assert posts[-1][1]["text"].startswith(
            "An error occurred. Try again in a moment."
        )
        assert "reply_markup" not in posts[-1][1]

    asyncio.run(run())


@pytest.mark.parametrize(
    "text,outputs",
    [
        ("/start", ["Hello!"]),
        ("hello", [RuntimeError("Unavailable")]),
        ("hello", ["  ", "NO_CORRECTION"]),
    ],
)
def test_openings_and_error_replies_have_no_button(setup, text, outputs):
    worker, llm, posts = setup
    llm.send.side_effect = outputs
    asyncio.run(deliver(worker, message(text)))
    assert posts
    assert all("reply_markup" not in p for _, p in posts)


@pytest.mark.parametrize(
    "tap",
    [
        callback("unrelated"),
        callback("rephrase:"),
        {"callback_query": {}},
        {"callback_query": {"id": "tap-1", "data": "rephrase:token"}},
    ],
)
def test_unknown_or_malformed_callback_is_safe(setup, tap):
    worker, llm, posts = setup
    assert asyncio.run(deliver(worker, tap)).status == 200
    llm.send.assert_not_awaited()
    assert all(method == "answerCallbackQuery" for method, _ in posts)


def test_new_sentence_during_rephrase_suppresses_old_alternative(setup):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message())
        data = button_data(posts)
        started, release = asyncio.Event(), asyncio.Event()

        async def delayed_alternative(messages):
            started.set()
            await release.wait()
            return "I enjoy coffee."

        llm.send.side_effect = delayed_alternative
        pending = asyncio.create_task(deliver(worker, callback(data)))
        await started.wait()
        llm.send.side_effect = ["New reply", "NO_CORRECTION"]
        await deliver(worker, message("I like tea."))
        posts.clear()
        release.set()
        assert (await pending).status == 200
        assert "no longer available" in posts[-1][1]["text"]
        assert "coffee" not in str(posts)

    asyncio.run(run())


def test_slow_old_reply_does_not_restore_latest_button(setup):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message("/feedback off"))
        posts.clear()
        started, release = asyncio.Event(), asyncio.Event()

        async def delayed_reply(messages):
            started.set()
            await release.wait()
            return "Old reply"

        llm.send.side_effect = delayed_reply
        pending = asyncio.create_task(deliver(worker, message("Old sentence.")))
        await started.wait()
        llm.send.side_effect = ["New reply"]
        await deliver(worker, message("Newest sentence."))
        data = button_data(posts)
        release.set()
        await pending
        assert "reply_markup" not in posts[-1][1]
        llm.send.side_effect = ["The newest wording."]
        posts.clear()
        await deliver(worker, callback(data))
        assert posts[-1][1]["text"] == "Another way: The newest wording."
        assert llm.send.call_args.args[0][1]["content"] == "Newest sentence."

    asyncio.run(run())


def test_button_only_on_persona_reply_not_automatic_correction(setup):
    worker, llm, posts = setup
    llm.send.side_effect = ["Nice!", "Use 'I like coffee.'"]
    asyncio.run(deliver(worker, message("I likes coffee.")))
    button_data(posts)
    assert len(posts) == 2
    assert posts[1] == ("sendMessage", {"chat_id": 123, "text": "Use 'I like coffee.'"})


def test_missing_context_without_prior_message_is_clear(setup):
    worker, llm, posts = setup
    assert asyncio.run(deliver(worker, callback("rephrase:missing"))).status == 200
    llm.send.assert_not_awaited()
    assert "no longer available" in posts[-1][1]["text"]


@pytest.mark.parametrize("method", ["answerCallbackQuery", "sendMessage"])
def test_callback_telegram_failure_returns_502(setup, monkeypatch, method):
    worker, llm, posts = setup

    async def run():
        await deliver(worker, message())
        data = button_data(posts)

        async def reject(token, requested_method, payload):
            if requested_method == method:
                raise ValueError("Telegram rejected request")

        monkeypatch.setattr(worker, "_telegram_request", reject)
        assert (await deliver(worker, callback(data))).status == 502

    asyncio.run(run())
