# pylint: disable=protected-access
"""
Tests pour les gestionnaires d'exceptions
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.exception_handlers import add_exception_handlers
from app.services.service_exceptions import (
    NotFoundException,
    FileTooBigException,
    StorageException
)


app = FastAPI()
add_exception_handlers(app)

@app.get("/raise-not-found")
def raise_not_found():
    """Route de test pour NotFoundException"""
    raise NotFoundException("Item not found")

@app.get("/raise-file-too-big")
def raise_file_too_big():
    """Route de test pour FileTooBigException"""
    raise FileTooBigException("File is too large")

@app.get("/raise-storage-error")
def raise_storage_error():
    """Route de test pour StorageException"""
    raise StorageException("Disk error")

client = TestClient(app)

def test_not_found_handler():
    """Vérifie que NotFoundException retourne 404"""
    response = client.get("/raise-not-found")
    assert response.status_code == 404
    assert response.json() == {"detail": "Resource not found: Item not found"}

def test_file_too_big_handler():
    """Vérifie que FileTooBigException retourne 413"""
    response = client.get("/raise-file-too-big")
    assert response.status_code == 413
    assert response.json() == {"detail": "File too big: File is too large"}

def test_storage_exception_handler():
    """Vérifie que StorageException retourne 422"""
    response = client.get("/raise-storage-error")
    assert response.status_code == 422
    assert response.json() == {"detail": "Disk error"}