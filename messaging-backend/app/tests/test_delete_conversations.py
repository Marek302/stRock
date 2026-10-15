import time
import pytest
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient
import jwt
from unittest.mock import MagicMock, AsyncMock
from app.tests.conftest import SECRET

def create_test_token(uid: str, permissions: list[str]) -> str:
    now = int(time.time())
    payload = {
        "uid": uid,
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "role": "user",
        "permissions": permissions,
        "email_verified": True,
        "sign_in_provider": "password",
        "iat": now,
        "exp": now + 3600,
        "auth_time": now,
        "iss": "https://securetoken.google.com/test-project",
        "aud": "test-project"
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

@pytest.mark.asyncio
async def test_delete_conversations_route(client: AsyncClient, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    token = create_test_token(test_user_id_1, ["messaging:create:self", "messaging:read:self"])
    headers = {"Authorization": f"Bearer {token}"}
    
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    create_resp = await client.post("/messaging/conversations", json={"listing_id": str(test_listing_id)}, headers=headers)
    assert create_resp.status_code == 201
    convo_id = create_resp.json()["id"]

    delete_resp = await client.request("DELETE", "/messaging/conversations", json={"conversation_ids": [convo_id]}, headers=headers)
    assert delete_resp.status_code == 204

    list_resp = await client.get("/messaging/conversations", headers=headers)
    assert list_resp.status_code == 200
    convos = list_resp.json()
    assert all(c["id"] != convo_id for c in convos)

@pytest.mark.asyncio
async def test_delete_conversations_unauthorized(client: AsyncClient, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    token1 = create_test_token(test_user_id_1, ["messaging:create:self", "messaging:read:self"])
    headers1 = {"Authorization": f"Bearer {token1}"}
    
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)

    create_resp = await client.post("/messaging/conversations", json={"listing_id": str(test_listing_id)}, headers=headers1)
    assert create_resp.status_code == 201
    convo_id = create_resp.json()["id"]

    user3_id = "different_user_id_abc_123"
    token3 = create_test_token(user3_id, ["messaging:create:self"])
    headers3 = {"Authorization": f"Bearer {token3}"}
    
    delete_resp = await client.request("DELETE", "/messaging/conversations", json={"conversation_ids": [convo_id]}, headers=headers3)
    assert delete_resp.status_code == 403
