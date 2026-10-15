"""
Tests pour le FirebaseTokenService
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
import time
import jwt
from cryptography.x509 import Certificate, CertificateBuilder
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
import datetime
from cryptography.x509.oid import NameOID

from app.services.firebase_token_service import FirebaseTokenService
from app.schemas.firebase_user_token import FirebaseUserToken

# Helpers pour générer des clés RSA de test
def generate_rsa_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024*2,
    )
    public_key = private_key.public_key()
    return private_key, public_key

def generate_self_signed_cert(private_key, public_key):
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"testcert"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        public_key
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=10)
    ).sign(private_key, hashes.SHA256())
    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

@pytest.fixture
def rsa_keys():
    """Fixture de test pour générer un jeu de clés RSA et son certificat PEM."""
    priv, pub = generate_rsa_keypair()
    cert_pem = generate_self_signed_cert(priv, pub)
    return {"priv": priv, "pub": pub, "cert": cert_pem}

@pytest.fixture
def mock_env(monkeypatch):
    """Configuration de base pour les tests."""
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setenv("FIREBASE_CERTS_URL", "http://test-url/certs")
    monkeypatch.setenv("ENVIRONMENT", "TEST")
    return monkeypatch

@pytest.mark.asyncio
async def test_firebase_service_missing_config():
    """
    Teste que le service lève une erreur 503 si la configuration Firebase est manquante.
    """
    with patch("os.getenv", return_value=None):
        service = FirebaseTokenService()
        with pytest.raises(HTTPException) as exc_info:
            await service.verify_id_token("fake-token")
        
        assert exc_info.value.status_code == 503

@pytest.mark.asyncio
async def test_get_public_keys_from_cache(mock_env):
    """
    Teste que les clés sont récupérées du cache si elles ne sont pas expirées.
    """
    service = FirebaseTokenService()
    service._cache = service.FirebaseKey({"kid-1": "cert-1"}, time.time() + 3600)
    
    keys = await service._get_public_keys()
    assert keys == {"kid-1": "cert-1"}

@pytest.mark.asyncio
async def test_get_public_keys_from_http(mock_env):
    """
    Teste la récupération des clés via HTTP si le cache est vide ou expiré.
    """
    service = FirebaseTokenService()
    
    mock_response = MagicMock()
    mock_response.headers = {"cache-control": "max-age=3600"}
    mock_response.json.return_value = {"kid-new": "cert-new"}
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    
    with patch("httpx.AsyncClient", return_value=mock_context):
        keys = await service._get_public_keys()
        
    assert keys == {"kid-new": "cert-new"}
    assert service._cache is not None
    assert service._cache.keys == {"kid-new": "cert-new"}

@pytest.mark.asyncio
async def test_verify_id_token_invalid_algorithm(mock_env):
    """
    Teste que la validation échoue avec un algorithme non supporté (ex: HS512 ici).
    """
    service = FirebaseTokenService()
    token = jwt.encode({"sub": "user1"}, ("1"*64), algorithm="HS512")
    
    with pytest.raises(HTTPException) as exc_info:
        await service.verify_id_token(token)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid algorithm"

@pytest.mark.asyncio
@patch("app.services.firebase_token_service.jwt.decode")
async def test_verify_id_token_cloud_token_valid(mock_decode, monkeypatch):
    """
    Teste la validation d'un cloud token interne (HS256) quand l'environnement n'est pas TEST.
    """
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.setenv("FIREBASE_CERTS_URL", "http://test-url/certs")
    monkeypatch.setenv("ENVIRONMENT", "PROD")
    monkeypatch.setenv("INTERNAL_API_SECRET", ("supersecret"*5))
    
    service = FirebaseTokenService()
    token = jwt.encode({"sub": "user123"}, ("supersecret"*5), algorithm="HS256", headers={"kid": "some-kid"})
    
    mock_decode.return_value = {"sub": "user123", "uid": "user123", "email": "test@test.com", "name": "Test"}
    
    result = await service.verify_id_token(token)
    assert isinstance(result, FirebaseUserToken)
    assert result.uid == "user123"

@pytest.mark.asyncio
async def test_verify_id_token_missing_kid(mock_env, rsa_keys):
    """
    Teste que le token est rejeté si le 'kid' est manquant dans le header ou inconnu.
    """
    service = FirebaseTokenService()
    # Encode with a real RSA key but a kid that won't match the mocked public keys
    token = jwt.encode({"sub": "user123"}, rsa_keys["priv"], algorithm="RS256", headers={"kid": "nonexistent-kid"})
    
    service._get_public_keys = AsyncMock(return_value={"unknown-kid": "cert"})
    
    with pytest.raises(HTTPException) as exc_info:
        await service.verify_id_token(token)
        
    assert exc_info.value.status_code == 401
    assert "kid" in exc_info.value.detail

@pytest.mark.asyncio
async def test_verify_id_token_invalid_jwt(mock_env, rsa_keys):
    """
    Teste le rejet d'un token malformé ou expiré (PyJWTError).
    """
    service = FirebaseTokenService()
    
    service._get_public_keys = AsyncMock(return_value={"my-kid": rsa_keys["cert"]})
    
    # Création d'un token qui va échouer car invalide
    token = jwt.encode({"sub": "user1"}, rsa_keys["priv"], algorithm="RS256", headers={"kid": "my-kid"})
    token += "invalid"
    
    with pytest.raises(HTTPException) as exc_info:
        await service.verify_id_token(token)
        
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_verify_id_token_valid_rs256(mock_env, rsa_keys):
    """
    Teste la validation complète d'un token Firebase standard (RS256).
    """
    service = FirebaseTokenService()
    
    service._get_public_keys = AsyncMock(return_value={"test-kid": rsa_keys["cert"]})
    
    payload = {
        "sub": "firebase-user",
        "aud": "test-project",
        "iss": "https://securetoken.google.com/test-project",
        "iat": time.time(),
        "exp": time.time() + 3600,
        "auth_time": time.time() - 100,
        "email": "user@test.com"
    }
    
    token = jwt.encode(payload, rsa_keys["priv"], algorithm="RS256", headers={"kid": "test-kid"})
    
    result = await service.verify_id_token(token)
    
    assert isinstance(result, FirebaseUserToken)
    assert result.uid == "firebase-user"
    assert result.email == "user@test.com"
