import pytest
import jwt
import time
import random
import string
from typing import List, Optional
from uuid import uuid4, UUID
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.messaging import Conversation, Message, LastMessage
from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.schemas.firebase_user_token import FirebaseUserToken
import app.services.firebase_token_service as fts
from app.tests.conftest import SECRET


class FakeMessagingRepository:
    """Faux repository pour les tests API (sans Mongo)."""

    def __init__(self):
        self.conversations = {}
        self.messages = {}
        self.pair_listing_index = {}

    def _get_pair_key(self, participants: List[str]) -> str:
        s_participants = sorted([str(p) for p in participants])
        return "|".join(s_participants)

    async def find_conversation_by_pair_listing(
        self,
        pair_key: str,
        listing_id: UUID,
    ) -> Optional[Conversation]:
        key = f"{pair_key}|{listing_id}"
        conv_id = self.pair_listing_index.get(key)
        if conv_id:
            return self.conversations.get(conv_id)
        return None

    async def insert_conversation(
        self,
        conversation: Conversation,
        pair_key: str,
    ) -> None:
        key = f"{pair_key}|{conversation.listing_id}"
        if key in self.pair_listing_index:
            raise ConflictError("Conversation already exists")

        self.conversations[conversation.id] = conversation
        self.pair_listing_index[key] = conversation.id

    async def list_conversations_for_user(
        self,
        user_id: str,
    ) -> List[Conversation]:
        result = []
        for conv in self.conversations.values():
            if user_id in conv.participants:
                result.append(conv)

        result.sort(
            key=lambda c: c.last_message.timestamp if c.last_message else c.created_at,
            reverse=True,
        )
        return result

    async def get_conversation(
        self,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        return self.conversations.get(conversation_id)

    async def get_by_listing_and_participants(
        self,
        listing_id : UUID,
        participants: List[str]
    ) -> Optional[Conversation]:
        pair_key = self._get_pair_key(participants)
        key = f"{pair_key}|{listing_id}"
        conv_id = self.pair_listing_index.get(key)
        if conv_id:
            return self.conversations.get(conv_id)
        return None

    async def list_messages(
        self,
        conversation_id: UUID,
    ) -> List[Message]:
        return [
            msg
            for msg in self.messages.values()
            if msg.conversation_id == conversation_id
        ]

    async def insert_message(
        self,
        message: Message,
    ) -> None:
        self.messages[message.id] = message

    async def set_conversation_last_message(
        self,
        conversation_id: UUID,
        last_message: LastMessage,
    ) -> None:
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.last_message = last_message

    async def mark_messages_read(
        self,
        conversation_id: UUID,
        user_id: str,
    ) -> int:
        count = 0
        for msg in self.messages.values():
            if msg.conversation_id == conversation_id and user_id not in msg.read_by:
                msg.read_by.append(user_id)
                count += 1
        return count


@pytest.fixture
def user1_id():
    """UID Firebase du premier utilisateur de test"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def user2_id():
    """UID Firebase du deuxième utilisateur de test"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def listing_id():
    """UUID de l'annonce de test"""
    return str(uuid4())

async def test_health(client):
    """Test du endpoint de vérification de santé"""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Rock-On! Messaging API"

def create_test_token(uid: str) -> str:
    now = int(time.time())
    payload = {
        "uid": uid,
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "role": "user",
        "permissions": ["messaging:create:self", "messaging:read:self", "messaging:send:self"],
        "email_verified": True,
        "sign_in_provider": "password",
        "iat": now,
        "exp": now + 3600,
        "auth_time": now,
        "iss": "https://securetoken.google.com/test-project",
        "aud": "test-project"
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")



async def test_create_conversation(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la création réussie d'une nouvelle conversation."""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert set(data["participants"]) == {user1_id, user2_id}
    assert data["listing_id"] == listing_id

async def test_create_conversation_conflict(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la création d'une conversation qui existe déjà."""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    response1 = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 201


    response2 = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response2.status_code == 409

async def test_get_conversation_for_listing(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la récupération d'une conversation par ID d'annonce."""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    create_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201

    response = await client.get(
        f"/messaging/conversations/{listing_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["listing_id"] == listing_id
    assert set(data["participants"]) == {user1_id, user2_id}

async def test_get_conversation_for_listing_not_found(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la récupération d'une conversation qui n'existe pas."""
    token = create_test_token(user1_id)
    
    mock_listing_service.get_by_id = AsyncMock(return_value=None)

    response = await client.get(
        f"/messaging/conversations/{listing_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404



async def test_send_message(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test d'envoi d'un message"""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    conv_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert conv_response.status_code == 201
    conversation_id = conv_response.json()["id"]
    
    response = await client.post(
        f"/messaging/conversations/{conversation_id}/messages",
        json={"content": "Bonjour! Est-ce que le livre est encore disponible?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert data["conversation_id"] == conversation_id
    assert data["sender_uid"] == user1_id
    assert data["content"] == "Bonjour! Est-ce que le livre est encore disponible?"
    assert data["timestamp"] is not None
    assert user1_id in data["read_by"]

async def test_send_message_with_images(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test d'envoi d'un message avec des IDs d'images"""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    conv_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    conversation_id = conv_response.json()["id"]
    
    image_ids = [str(uuid4()), str(uuid4())]
    response = await client.post(
        f"/messaging/conversations/{conversation_id}/messages",
        json={
            "content": "Regarde ces photos",
            "image_ids": image_ids
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["image_ids"] == image_ids
    assert data["content"] == "Regarde ces photos"

async def test_list_messages(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test du listage des messages d'une conversation"""
    token1 = create_test_token(user1_id)
    token2 = create_test_token(user2_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    conv_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert conv_response.status_code == 201
    conversation_id = conv_response.json()["id"]
    
    await client.post(
        f"/messaging/conversations/{conversation_id}/messages",
        json={"content": "Premier message"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    await client.post(
        f"/messaging/conversations/{conversation_id}/messages",
        json={"content": "Deuxième message"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    response = await client.get(
        f"/messaging/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "Premier message"
    assert messages[1]["content"] == "Deuxième message"



async def test_get_conversation_success(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la récupération réussie d'une conversation"""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    create_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201

    response = await client.get(
        f"/messaging/conversations/by-listing-and-participant?listing_id={listing_id}&buyer_id={user2_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data["participants"]) == {user1_id, user2_id}
    assert data["listing_id"] == listing_id

async def test_get_conversation_not_found(client, user1_id, user2_id):
    """Test de la récupération d'une conversation inexistante"""
    token = create_test_token(user1_id)
    non_existent_listing_id = str(uuid4())

    response = await client.get(
        f"/messaging/conversations/by-listing-and-participant?listing_id={non_existent_listing_id}&buyer_id={user2_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404

async def test_list_messages_unauthorized(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test d'accès non autorisé aux messages d'une conversation"""
    token1 = create_test_token(user1_id)
    user3_id = "".join(random.choices(string.ascii_letters + string.digits, k=28))
    token3 = create_test_token(user3_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    conv_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token1}"}
    )
    conversation_id = conv_response.json()["id"]
    
    response = await client.get(
        f"/messaging/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token3}"}
    )
    assert response.status_code == 403

async def test_mark_read(client, user1_id, user2_id, listing_id, mock_listing_service):
    token1 = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    conv_response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token1}"}
    )
    conversation_id = conv_response.json()["id"]
    
    response = await client.post(
        f"/messaging/conversations/{conversation_id}/read",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 200
    assert "updated" in response.json()

async def test_mark_read_not_found(client, user1_id):
    token1 = create_test_token(user1_id)
    fake_id = uuid4()
    response = await client.post(
        f"/messaging/conversations/{fake_id}/read",
        headers={"Authorization": f"Bearer {token1}"}
    )
    assert response.status_code == 404

@pytest.mark.skip
async def test_websocket_connection(client, user1_id, user2_id, listing_id, mock_listing_service):
    token = create_test_token(user1_id)
    
    with patch.object(fts._firebase_service, "verify_id_token", new_callable=AsyncMock) as mock_verify:
        now = int(time.time())
        payload = {
            "uid": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://pic",
            "role": "user",
            "permissions": ["messaging:create:self", "messaging:read:self", "messaging:send:self"],
            "email_verified": True,
            "sign_in_provider": "password",
            "iat": now - 10,
            "exp": now + 3600,
            "auth_time": now - 10,
            "iss": f"https://securetoken.google.com/test-project",
            "aud": "test-project"
        }
        mock_verify.return_value = FirebaseUserToken(**payload)
        mock_listing = MagicMock()
        mock_listing.user_id = user2_id
        mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

        # Use the existing client to create a conversation
        conv_response = await client.post(
            "/messaging/conversations",
            json={"listing_id": listing_id},
            headers={"Authorization": f"Bearer {token}"}
        )
        conversation_id = conv_response.json()["id"]
        
        from fastapi.testclient import TestClient
        from main import app as main_app
        # We use TestClient because AsyncClient doesn't support websocket_connect easily without extra dependencies
        with TestClient(client.app) as test_client:
            # Mock dependencies in the app instance used by TestClient are already set in conftest.py
            with test_client.websocket_connect(f"/messaging/ws/conversations/{conversation_id}?token={token}") as websocket:
                # Just connect and close
                pass

async def test_create_conversation_and_delete_listing_success(client, user1_id, listing_id, mock_listing_service):
    """Test de la suppression réussie des conversations d'une annonce."""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user1_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    response = await client.post(
        "/messaging/conversations",
        json={"listing_id": listing_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201

    response = await client.delete(
        f"/messaging/listing/{listing_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204

async def test_delete_listing_forbidden(client, user1_id, user2_id, listing_id, mock_listing_service):
    """Test de la suppression refusée des conversations d'une annonce si l'utilisateur n'est pas le vendeur."""
    token = create_test_token(user1_id)
    
    mock_listing = MagicMock()
    mock_listing.user_id = user2_id
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    response = await client.delete(
        f"/messaging/listing/{listing_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Acces refuse a cette annonce."
