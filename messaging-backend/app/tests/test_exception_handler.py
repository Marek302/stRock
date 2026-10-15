# app/tests/test_exception_handler.py
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.exception_handler import add_exception_handlers
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/not_found")
    def raise_not_found():
        raise NotFoundError("Test Not Found")

    @app.get("/forbidden")
    def raise_forbidden():
        raise ForbiddenError("Test Forbidden")

    @app.get("/conflict")
    def raise_conflict():
        raise ConflictError("Test Conflict")

    @app.get("/value_error")
    def raise_value_error():
        raise ValueError("Test Value Error")

    @app.get("/unhandled")
    def raise_unhandled():
        raise Exception("Test Unhandled Exception")

    add_exception_handlers(app)
    return app


@pytest.fixture
def client(app: FastAPI):
    return TestClient(app, raise_server_exceptions=False)


def test_not_found_handler(client: TestClient):
    response = client.get("/not_found")
    assert response.status_code == 404
    assert response.json() == {"detail": "Test Not Found"}


def test_forbidden_handler(client: TestClient):
    response = client.get("/forbidden")
    assert response.status_code == 403
    assert response.json() == {"detail": "Test Forbidden"}


def test_conflict_handler(client: TestClient):
    response = client.get("/conflict")
    assert response.status_code == 409
    assert response.json() == {"detail": "Test Conflict"}


def test_value_error_handler(client: TestClient):
    response = client.get("/value_error")
    assert response.status_code == 400
    assert response.json() == {"detail": "Test Value Error"}


def test_general_exception_handler(client: TestClient):
    response = client.get("/unhandled")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}

