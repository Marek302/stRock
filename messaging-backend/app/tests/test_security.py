import pytest
from fastapi import HTTPException, Depends, FastAPI
from fastapi.testclient import TestClient
from app.core.security import with_claims, with_any_claim
from app.schemas.firebase_user_token import FirebaseUserToken
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_token():
    return FirebaseUserToken(
        uid="user123",
        email="test@example.com",
        name="Test User",
        picture="http://pic",
        role="user",
        permissions=["perm1", "perm2"],
        email_verified=True,
        sign_in_provider="password",
        iat=123,
        exp=456,
        auth_time=789,
        iss="iss",
        aud="aud"
    )

@pytest.mark.asyncio
async def test_with_claims_success(mock_token):
    token_service = MagicMock()
    token_service.verify_id_token = AsyncMock(return_value=mock_token)
    
    dependency = with_claims(["perm1"])
    result = await dependency(encoded_bearer="valid-token", token_service=token_service)
    
    assert result == mock_token
    token_service.verify_id_token.assert_called_once_with(token="valid-token")

@pytest.mark.asyncio
async def test_with_claims_missing_permission(mock_token):
    token_service = MagicMock()
    token_service.verify_id_token = AsyncMock(return_value=mock_token)
    
    dependency = with_claims(["missing_perm"])
    with pytest.raises(HTTPException) as exc:
        await dependency(encoded_bearer="valid-token", token_service=token_service)
    
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_with_any_claim_success(mock_token):
    token_service = MagicMock()
    token_service.verify_id_token = AsyncMock(return_value=mock_token)
    
    dependency = with_any_claim(["perm2", "other"])
    result = await dependency(encoded_bearer="valid-token", token_service=token_service)
    
    assert result == mock_token

@pytest.mark.asyncio
async def test_with_any_claim_failure(mock_token):
    token_service = MagicMock()
    token_service.verify_id_token = AsyncMock(return_value=mock_token)
    
    dependency = with_any_claim(["other"])
    with pytest.raises(HTTPException) as exc:
        await dependency(encoded_bearer="valid-token", token_service=token_service)
    
    assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_with_claims_no_token():
    token_service = MagicMock()
    dependency = with_claims(["perm1"])
    with pytest.raises(HTTPException) as exc:
        await dependency(encoded_bearer=None, token_service=token_service)
    assert exc.value.status_code == 401
