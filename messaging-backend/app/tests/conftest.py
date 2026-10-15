"""
Configuration globale de pytest pour le service de messagerie.
Définit les fixtures partagées et la configuration des tests.
"""
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock
import jwt
import random
import string
from urllib.parse import urlparse
import pytest
from uuid import uuid4
from typing import AsyncGenerator
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from testcontainers.mongodb import MongoDbContainer
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.db import get_settings
from app.core.deps import get_messaging_service
from app.schemas.firebase_user_token import FirebaseUserToken
from app.services.firebase_token_service import get_firebase_token_service
from app.services.listing_service import ListingService
from app.services.messaging_repo import MongoMessagingRepository
from app.services.messaging_service import MessagingService
from app.core.security import oauth2_scheme
import app.services.firebase_token_service as fts

from main import create_app
from app.services.ws_manager import ConversationWebSocketManager

SECRET = "SUPER-LONG-SECRET-KEY-TO-SUPPRESS-WARNINGS"


def _configure_testcontainers_host_override() -> None:
    docker_host = os.getenv("DOCKER_HOST", "")
    if os.getenv("CI") and "docker" in docker_host:
        os.environ.setdefault("TESTCONTAINERS_HOST_OVERRIDE", "docker")


_configure_testcontainers_host_override()


@pytest.fixture(scope="session")
def mongodb_container():
    with MongoDbContainer("mongo:6.0") as mongo:
        yield mongo

@pytest.fixture(scope="session")
def mock_settings(mongodb_container, tmp_path_factory):
    photo_root = tmp_path_factory.mktemp("photos")
    parsed_uri = urlparse(mongodb_container.get_connection_url())
    mongo_host = parsed_uri.hostname or str(mongodb_container.get_container_host_ip())
    mongo_port = parsed_uri.port or int(mongodb_container.get_exposed_port(27017))

    os.environ.update({
        "MONGO_USER": "test_user",
        "MONGO_PASSWORD": "test_password",
        "MONGO_DB_NAME": "test_db",
        "MONGO_HOST": str(mongo_host),
        "MONGO_PORT": str(mongo_port),
        "ENV": "TEST",
        "ENVIRONMENT": "TEST",
        "FIREBASE_PROJECT_ID": "test-project",
        "FIREBASE_CERTS_URL": "test.com",
        "PHOTO_SAVE_ROOT_MESSAGING": str(photo_root)
    })
  
    get_settings.cache_clear()
    return get_settings()

@pytest.fixture(scope="session")
async def database(mongodb_container, mock_settings):
    client = AsyncIOMotorClient(mongodb_container.get_connection_url())
    db = client[mock_settings.mongo_db_name]
    yield db
    client.close()

@pytest.fixture
def mock_listing_service():
    """Fixture pour mocker le ListingService."""
    return MagicMock(spec=ListingService)

@pytest.fixture
def mock_image_service():
    """Fixture pour mocker le ImageService."""
    service = MagicMock()
    service.get_by_id = AsyncMock()
    service.delete = AsyncMock()
    
    async def fake_create_image(conversation):
        from app.models.image import Image
        img_id = uuid4()
        return Image(
            id=img_id,
            image_path=f"/{conversation.id}/{img_id}",
            conversation=conversation
        )
    service.create_image = AsyncMock(side_effect=fake_create_image)
    return service

@pytest.fixture
async def client(database, mock_listing_service, mock_image_service) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    real_repo = MongoMessagingRepository(database)
    await real_repo.ensure_indexes()
    
    real_service = MessagingService(real_repo, mock_image_service)
    app.state.messaging_service = real_service
    app.state.image_service = mock_image_service
    app.state.ws_manager = ConversationWebSocketManager()

    async def mock_oauth_dependency(request: Request):
        auth = request.headers.get("Authorization")
        return auth.split(" ", 1)[1] if auth else None

    class MockService:
        async def verify_id_token(self, token: str):
            payload = jwt.decode(
                token, 
                SECRET, 
                algorithms=["HS256"], 
                options={"verify_aud": False}
            )
            return FirebaseUserToken(**payload)
            
    
    mock_token_service = MockService()
    app.dependency_overrides[get_messaging_service] = lambda: real_service
    app.dependency_overrides[get_firebase_token_service] = lambda: mock_token_service
    app.dependency_overrides[oauth2_scheme] = mock_oauth_dependency
    app.dependency_overrides[ListingService.get_listing_service] = lambda: mock_listing_service

    original_get_service = fts.get_firebase_token_service
    fts.get_firebase_token_service = AsyncMock(return_value=mock_token_service)
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        ac.app = app
        yield ac

    fts.get_firebase_token_service = original_get_service
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_id_1():
    """UUID du premier utilisateur de test"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def test_user_id_2():
    """UUID du deuxième utilisateur de test"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def test_user_id_3():
    """UUID du troisième utilisateur de test (pour tests d'autorisation)"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def test_listing_id():
    """UUID d'un listing de test"""
    return uuid4()


@pytest.fixture
def test_listing_id_2():
    """UUID d'un second listing de test"""
    return uuid4()


# Configuration des markers pytest
def pytest_configure(config):
    """
    Configuration des markers personnalisés pour pytest.
    """
    config.addinivalue_line(
        "markers", "integration: marque les tests d'intégration nécessitant une DB"
    )
    config.addinivalue_line(
        "markers", "unit: marque les tests unitaires isolés"
    )
    config.addinivalue_line(
        "markers", "slow: marque les tests lents"
    )
