"""
Tests pour les dépendances de sécurité (app/core/security.py)
"""
import pytest
import time
from unittest.mock import AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import with_claims, with_any_claim, optional_with_claims
from app.schemas.firebase_user_token import FirebaseUserToken


@pytest.fixture
def mock_token_service():
    """Fixture pour mocker le FirebaseTokenService."""
    return AsyncMock()


@pytest.fixture
def valid_token():
    """Fixture retournant un token utilisateur valide avec des permissions."""
    return FirebaseUserToken(
        uid="user123",
        email="test@test.com",
        name="Test User",
        picture="",
        role="user",
        permissions=["read:items", "write:items"],
        email_verified=True,
        sign_in_provider="password",
        iat=int(time.time()),
        exp=int(time.time()) + 3600,
        auth_time=int(time.time()) - 100,
        iss="test-issuer",
        aud="test-audience"
    )


# --- Tests pour with_claims ---

@pytest.mark.asyncio
async def test_with_claims_missing_bearer(mock_token_service):
    """
    Teste que l'accès est refusé (401) si le token bearer est manquant.
    """
    dependency = with_claims(["read:items"])
    with pytest.raises(HTTPException) as exc_info:
        await dependency(encoded_bearer=None, token_service=mock_token_service)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token"


@pytest.mark.asyncio
async def test_with_claims_success(mock_token_service, valid_token):
    """
    Teste que le token est retourné si toutes les permissions requises sont présentes.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = with_claims(["read:items", "write:items"])
    
    result = await dependency(encoded_bearer="token123", token_service=mock_token_service)
    
    assert result == valid_token
    mock_token_service.verify_id_token.assert_called_once_with(token="token123")


@pytest.mark.asyncio
async def test_with_claims_missing_permissions(mock_token_service, valid_token):
    """
    Teste que l'accès est refusé (403) si le token n'a pas toutes les permissions requises.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = with_claims(["read:items", "delete:items"]) # delete:items est manquant
    
    with pytest.raises(HTTPException) as exc_info:
        await dependency(encoded_bearer="token123", token_service=mock_token_service)
        
    assert exc_info.value.status_code == 403
    assert "Missing required permissions" in exc_info.value.detail


# --- Tests pour with_any_claim ---

@pytest.mark.asyncio
async def test_with_any_claim_missing_bearer(mock_token_service):
    """
    Teste que l'accès est refusé (401) si le token bearer est manquant.
    """
    dependency = with_any_claim(["read:items"])
    with pytest.raises(HTTPException) as exc_info:
        await dependency(encoded_bearer="", token_service=mock_token_service)
        
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token"


@pytest.mark.asyncio
async def test_with_any_claim_success(mock_token_service, valid_token):
    """
    Teste que le token est retourné si au moins une permission requise est présente.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = with_any_claim(["delete:items", "write:items"]) # write:items est présent
    
    result = await dependency(encoded_bearer="token123", token_service=mock_token_service)
    
    assert result == valid_token


@pytest.mark.asyncio
async def test_with_any_claim_missing_all_permissions(mock_token_service, valid_token):
    """
    Teste que l'accès est refusé (403) si le token n'a aucune des permissions requises.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = with_any_claim(["delete:items", "admin"]) 
    
    with pytest.raises(HTTPException) as exc_info:
        await dependency(encoded_bearer="token123", token_service=mock_token_service)
        
    assert exc_info.value.status_code == 403
    assert "Missing any required permission" in exc_info.value.detail


# --- Tests pour optional_with_claims ---

@pytest.mark.asyncio
async def test_optional_with_claims_missing_credentials(mock_token_service):
    """
    Teste que None est retourné si les credentials HTTPAuthorizationCredentials sont manquants.
    """
    dependency = optional_with_claims(["read:items"])
    result = await dependency(credentials=None, token_service=mock_token_service)
    
    assert result is None


@pytest.mark.asyncio
async def test_optional_with_claims_missing_token_string(mock_token_service):
    """
    Teste que None est retourné si la chaîne du token est vide.
    """
    dependency = optional_with_claims(["read:items"])
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
    result = await dependency(credentials=creds, token_service=mock_token_service)
    
    assert result is None


@pytest.mark.asyncio
async def test_optional_with_claims_success(mock_token_service, valid_token):
    """
    Teste que le token est retourné si valide et contient les bonnes permissions.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = optional_with_claims(["read:items"])
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token123")
    
    result = await dependency(credentials=creds, token_service=mock_token_service)
    
    assert result == valid_token


@pytest.mark.asyncio
async def test_optional_with_claims_missing_permissions(mock_token_service, valid_token):
    """
    Teste que None est retourné si le token n'a pas les permissions requises.
    """
    mock_token_service.verify_id_token.return_value = valid_token
    dependency = optional_with_claims(["admin"])
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token123")
    
    result = await dependency(credentials=creds, token_service=mock_token_service)
    
    assert result is None


@pytest.mark.asyncio
async def test_optional_with_claims_invalid_token(mock_token_service):
    """
    Teste que None est retourné si la vérification du token échoue (exception).
    """
    mock_token_service.verify_id_token.side_effect = Exception("Invalid token")
    dependency = optional_with_claims(["read:items"])
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad_token")
    
    result = await dependency(credentials=creds, token_service=mock_token_service)
    
    assert result is None
