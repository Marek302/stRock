import jwt
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from testcontainers.postgres import PostgresContainer
from app.schemas.firebase_user_token import FirebaseUserToken
from app.services.firebase_token_service import get_firebase_token_service
from app.services.messaging_service import MessagingService
from app.core import db as core_db
from main import create_application
from app.core.db import get_session
from app.core.security import oauth2_scheme

@pytest.fixture
def test_app():
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("ENVIRONMENT", "TEST")
        return create_application()

@pytest.fixture(scope="session")
def db_engine():
    """Démarre Postgres une seule fois pour toute la session de test."""
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url().replace("postgresql://", "postgresql+psycopg2://")
        engine = create_engine(url)
        core_db.engine = engine
        SQLModel.metadata.create_all(engine)
        yield engine
        SQLModel.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Fournit une session propre pour chaque test et nettoie après."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()

SECRET_KEY = "super-long-testing-secret-key-to-suppress-warnings"
ALGORITHM = "HS256"

@pytest.fixture
def client(test_app, db_session: Session):
    """Exposer la fixture FastAPI TestClient à tous les tests."""
    def get_session_override():
        yield db_session
    async def mock_oauth_dependency(request: Request):
        auth = request.headers.get("Authorization")
        return auth.split(" ", 1)[1] if auth else None
    class MockService:
        async def verify_id_token(self, token: str):
            payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "verify_aud": False
                }
            )
            return FirebaseUserToken(**payload)

    class MockMessagingService:
        async def get_message_by_post_and_participant(self, buyer_id, encoded_token, post_id):
            return None
        async def delete_by_post_id(self, post_id, encoded_token):
            pass

    test_app.dependency_overrides[get_session] = get_session_override
    test_app.dependency_overrides[get_firebase_token_service] = lambda: MockService()
    test_app.dependency_overrides[MessagingService.get_messaging_service] = lambda: MockMessagingService()
    test_app.dependency_overrides[oauth2_scheme] = mock_oauth_dependency
    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()
