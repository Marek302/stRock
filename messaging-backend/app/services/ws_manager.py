from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket

from app.models.messaging import Message


class ConversationWebSocketManager:
    """Tracks websocket clients by conversation and broadcasts new messages."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, conversation_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        key = str(conversation_id)
        async with self._lock:
            self._connections[key].add(websocket)

    async def disconnect(self, conversation_id: UUID, websocket: WebSocket) -> None:
        key = str(conversation_id)
        async with self._lock:
            sockets = self._connections.get(key)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(key, None)

    async def broadcast_message(self, message: Message) -> None:
        key = str(message.conversation_id)
        async with self._lock:
            recipients = list(self._connections.get(key, set()))

        if not recipients:
            return

        payload = {
            "type": "message.created",
            "data": message.model_dump(mode="json"),
        }
        disconnected: list[WebSocket] = []
        for socket in recipients:
            try:
                await socket.send_json(payload)
            except Exception:
                disconnected.append(socket)

        for socket in disconnected:
            await self.disconnect(message.conversation_id, socket)
