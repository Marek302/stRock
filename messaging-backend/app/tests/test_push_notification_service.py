from uuid import uuid4

import pytest

from app.services.push_notification_service import PushNotificationService


def test_build_message_preview_variants():
    assert PushNotificationService._build_message_preview("") == "Vous avez reçu une image."
    assert PushNotificationService._build_message_preview("  ") == "Vous avez reçu une image."
    assert PushNotificationService._build_message_preview("hello") == "hello"
    long_text = "a" * 100
    preview = PushNotificationService._build_message_preview(long_text)
    assert preview.endswith("...")
    assert len(preview) == 80


def test_topic_for_user():
    assert PushNotificationService._topic_for_user("abc") == "user_abc"


@pytest.mark.asyncio
async def test_send_new_message_notification_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(
        PushNotificationService,
        "_initialize_firebase",
        lambda self: setattr(self, "enabled", False),
    )
    service = PushNotificationService()

    called = {"send": False}

    def _fake_send(_):
        called["send"] = True

    monkeypatch.setattr("app.services.push_notification_service.messaging.send", _fake_send)

    await service.send_new_message_notification(
        receiver_uid="B" * 28,
        sender_uid="A" * 28,
        conversation_id=uuid4(),
        content="hello",
        sender_name="Alice",
        article_title="Book title",
    )

    assert called["send"] is False


@pytest.mark.asyncio
async def test_send_new_message_notification_builds_expected_payload(monkeypatch):
    monkeypatch.setattr(
        PushNotificationService,
        "_initialize_firebase",
        lambda self: setattr(self, "enabled", True),
    )
    service = PushNotificationService()

    captured = {}

    class _FakeNotification:
        def __init__(self, title, body):
            self.title = title
            self.body = body

    class _FakeMessage:
        def __init__(self, notification, data, topic):
            self.notification = notification
            self.data = data
            self.topic = topic

    def _fake_send(msg):
        captured["message"] = msg
        return "ok"

    async def _fake_to_thread(func, arg):
        return func(arg)

    monkeypatch.setattr(
        "app.services.push_notification_service.messaging.Notification",
        _FakeNotification,
    )
    monkeypatch.setattr(
        "app.services.push_notification_service.messaging.Message",
        _FakeMessage,
    )
    monkeypatch.setattr("app.services.push_notification_service.messaging.send", _fake_send)
    monkeypatch.setattr("app.services.push_notification_service.asyncio.to_thread", _fake_to_thread)

    conversation_id = uuid4()
    await service.send_new_message_notification(
        receiver_uid="B" * 28,
        sender_uid="A" * 28,
        conversation_id=conversation_id,
        content="hello there",
        sender_name="Alice",
        article_title="Book title",
    )

    sent = captured["message"]
    assert sent.topic == f"user_{'B' * 28}"
    assert sent.notification.title == "Book title"
    assert sent.notification.body == "Alice: hello there"
    assert sent.data["type"] == "new_message"
    assert sent.data["conversation_id"] == str(conversation_id)
    assert sent.data["sender_uid"] == "A" * 28
