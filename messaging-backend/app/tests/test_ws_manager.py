from datetime import datetime, UTC
from uuid import uuid4

import pytest

from app.models.messaging import Message
from app.services.ws_manager import ConversationWebSocketManager


class _FakeWebSocket:
    def __init__(self, should_fail: bool = False):
        self.accepted = False
        self.should_fail = should_fail
        self.sent_payloads = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        if self.should_fail:
            raise RuntimeError("socket send failed")
        self.sent_payloads.append(payload)


def _build_message(conversation_id):
    uid = "A" * 28
    return Message(
        id=uuid4(),
        conversation_id=conversation_id,
        sender_uid=uid,
        content="hello",
        image_ids=[],
        timestamp=datetime.now(UTC),
        read_by=[uid],
    )


@pytest.mark.asyncio
async def test_connect_and_disconnect_lifecycle():
    manager = ConversationWebSocketManager()
    conversation_id = uuid4()
    ws = _FakeWebSocket()

    await manager.connect(conversation_id, ws)
    assert ws.accepted is True

    key = str(conversation_id)
    assert key in manager._connections
    assert ws in manager._connections[key]

    await manager.disconnect(conversation_id, ws)
    assert key not in manager._connections


@pytest.mark.asyncio
async def test_broadcast_message_sends_to_all_connected_clients():
    manager = ConversationWebSocketManager()
    conversation_id = uuid4()
    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()

    await manager.connect(conversation_id, ws1)
    await manager.connect(conversation_id, ws2)

    message = _build_message(conversation_id)
    await manager.broadcast_message(message)

    assert len(ws1.sent_payloads) == 1
    assert len(ws2.sent_payloads) == 1
    assert ws1.sent_payloads[0]["type"] == "message.created"
    assert ws1.sent_payloads[0]["data"]["content"] == "hello"


@pytest.mark.asyncio
async def test_broadcast_disconnects_failed_socket():
    manager = ConversationWebSocketManager()
    conversation_id = uuid4()
    good_ws = _FakeWebSocket()
    bad_ws = _FakeWebSocket(should_fail=True)

    await manager.connect(conversation_id, good_ws)
    await manager.connect(conversation_id, bad_ws)

    message = _build_message(conversation_id)
    await manager.broadcast_message(message)

    key = str(conversation_id)
    assert key in manager._connections
    assert good_ws in manager._connections[key]
    assert bad_ws not in manager._connections[key]
