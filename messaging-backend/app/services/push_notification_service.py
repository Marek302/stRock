import asyncio
import json
import logging
import os
from typing import Optional
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, messaging


logger = logging.getLogger(__name__)


class PushNotificationService:
    def __init__(self):
        self.enabled = False
        self._initialize_firebase()

    def _initialize_firebase(self) -> None:
        try:
            firebase_admin.get_app()
            self.enabled = True
            return
        except ValueError:
            pass

        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        try:
            if service_account_json:
                service_account = json.loads(service_account_json)
                cred = credentials.Certificate(service_account)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
            self.enabled = True
        except Exception as exc:
            self.enabled = False
            logger.warning("Firebase app initialization failed; push notifications disabled: %s", exc)

    @staticmethod
    def _topic_for_user(uid: str) -> str:
        return f"user_{uid}"

    @staticmethod
    def _build_message_preview(content: str) -> str:
        cleaned = (content or "").strip()
        if not cleaned:
            return "Vous avez reçu une image."
        if len(cleaned) <= 80:
            return cleaned
        return f"{cleaned[:77]}..."

    async def send_new_message_notification(
        self,
        receiver_uid: str,
        sender_uid: str,
        conversation_id: UUID,
        content: str,
        sender_name: Optional[str] = None,
        article_title: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return

        topic = self._topic_for_user(receiver_uid)
        preview = self._build_message_preview(content)
        sender_display = (sender_name).strip()
        article_display = (article_title).strip()

        notification = messaging.Notification(
            title=article_display,
            body=f"{sender_display}: {preview}",
        )

        message = messaging.Message(
            notification=notification,
            data={
                "type": "new_message",
                "conversation_id": str(conversation_id),
                "sender_uid": sender_uid,
                "sender_name": sender_display,
                "article_title": article_display,
                "message_content": preview,
            },
            topic=topic,
        )

        await asyncio.to_thread(messaging.send, message)
