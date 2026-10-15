import pytest
import time
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.firebase_token_service import FirebaseTokenService
from app.schemas.firebase_user_token import FirebaseUserToken
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
import datetime

@pytest.fixture
def firebase_service():
    with patch.dict('os.environ', {
        'FIREBASE_PROJECT_ID': 'test-project',
        'FIREBASE_CERTS_URL': 'http://test-certs'
    }):
        service = FirebaseTokenService()
        return service

@pytest.fixture
def key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

@pytest.fixture
def cert_pem(key_pair):
    private_key, public_key = key_pair
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"test-project"),
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
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    return cert.public_bytes(serialization.Encoding.PEM).decode()

async def test_get_public_keys_caching(firebase_service, cert_pem):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"cache-control": "max-age=3600"}
        mock_response.json.return_value = {"kid1": cert_pem}
        mock_get.return_value = mock_response
        
        # First call - fetches from URL
        keys1 = await firebase_service._get_public_keys()
        assert keys1 == {"kid1": cert_pem}
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        keys2 = await firebase_service._get_public_keys()
        assert keys2 == {"kid1": cert_pem}
        assert mock_get.call_count == 1

async def test_verify_id_token_success(firebase_service, key_pair, cert_pem):
    private_key, public_key = key_pair
    now = int(time.time())
    payload = {
        "sub": "user123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "http://pic",
        "role": "user",
        "permissions": ["read"],
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
        "iat": now - 10,
        "exp": now + 3600,
        "auth_time": now - 10,
        "iss": f"https://securetoken.google.com/test-project",
        "aud": "test-project"
    }
    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": "kid1"})
    
    with patch.object(firebase_service, '_get_public_keys', AsyncMock(return_value={"kid1": cert_pem})):
        result = await firebase_service.verify_id_token(token)
        assert isinstance(result, FirebaseUserToken)
        assert result.uid == "user123"

async def test_verify_id_token_missing_config(firebase_service):
    firebase_service.project_id = None
    with pytest.raises(HTTPException) as exc:
        await firebase_service.verify_id_token("some-token")
    assert exc.value.status_code == 503

async def test_verify_id_token_invalid_alg(firebase_service):
    token = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        await firebase_service.verify_id_token(token)
    assert exc.value.status_code == 401
    assert "Invalid algorithm" in exc.value.detail

async def test_verify_id_token_invalid_kid(firebase_service, cert_pem):
    private_key = rsa.generate_private_key(65537, 2048, default_backend())
    token = jwt.encode({"sub": "123"}, private_key, algorithm="RS256", headers={"kid": "wrong-kid"})
    
    with patch.object(firebase_service, '_get_public_keys', AsyncMock(return_value={"kid1": cert_pem})):
        with pytest.raises(HTTPException) as exc:
            await firebase_service.verify_id_token(token)
        assert exc.value.status_code == 401
        assert "Invalid or missing kid" in exc.value.detail
