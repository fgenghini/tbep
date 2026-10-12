import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest

from messages.rephrase_processor import RephraseProcessor
from state.user_state_store import SentenceContext
from state.user_state_store_memory import UserStateStoreMemory


def processor():
    store = UserStateStoreMemory()
    store.set_persona(1, "a pirate")
    store.set_topic(1, "sailing")
    store.set_feedback(1, "off")
    store.append_turn(1, "user", "Private older conversation")
    store.get(1).latest_sentence = SentenceContext("token", "I like coffee.", 10)
    client = MagicMock()
    client.send = AsyncMock(return_value="  I enjoy coffee.  ")
    factory = MagicMock()
    factory.create.return_value = client
    return RephraseProcessor(store, factory), store, client


def test_rephrase_uses_only_latest_text_and_preserves_state():
    rephrase, store, client = processor()
    before = deepcopy(store.get(1))
    result = asyncio.run(rephrase.process(1, 10, "token"))
    assert result == "Another way: I enjoy coffee."
    assert store.get(1) == before
    messages = client.send.call_args.args[0]
    assert len(messages) == 2
    assert messages[1] == {"role": "user", "content": "I like coffee."}
    assert "pirate" not in str(messages)
    assert "Private older conversation" not in str(messages)


@pytest.mark.parametrize(
    "user_id,chat_id,token", [(2, 10, "token"), (1, 11, "token"), (1, 10, "old")]
)
def test_rephrase_rejects_mismatched_context_without_model_call(
    user_id, chat_id, token
):
    rephrase, store, client = processor()
    result = asyncio.run(rephrase.process(user_id, chat_id, token))
    assert "no longer available" in result
    client.send.assert_not_awaited()


def test_history_reset_invalidates_rephrase_context():
    rephrase, store, client = processor()
    store.reset_history(1)
    assert "no longer available" in asyncio.run(rephrase.process(1, 10, "token"))
    client.send.assert_not_awaited()
    assert store.get(1).feedback == "off"
    assert store.get(1).persona == "a pirate"
