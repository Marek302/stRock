import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from app.tests.test_api import create_test_token

TEST_IMAGES_DIR = Path(__file__).parent / "test_images"

@pytest.fixture
def auth_headers(test_user_id_1):
    token = create_test_token(test_user_id_1)
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_upload_jpg_success(client, auth_headers, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    """Test upload d'une image JPG valide"""
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    conv_res = await client.post(
        "/messaging/conversations",
        json={"listing_id": str(test_listing_id)},
        headers=auth_headers
    )
    conversation_id = conv_res.json()["id"]
    
    image_path = TEST_IMAGES_DIR / "test-jpg.jpg"
    with open(image_path, "rb") as f:
        files = {"image": ("test-jpg.jpg", f, "image/jpeg")}
        response = await client.post(
            f"/messaging/images/{conversation_id}/images",
            files=files,
            headers=auth_headers
        )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["image_path"].startswith(f"/{conversation_id}/")

@pytest.mark.asyncio
async def test_upload_webp_success(client, auth_headers, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    """Test upload d'une image WebP valide"""
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    conv_res = await client.post(
        "/messaging/conversations",
        json={"listing_id": str(test_listing_id)},
        headers=auth_headers
    )
    conversation_id = conv_res.json()["id"]
    
    image_path = TEST_IMAGES_DIR / "test-webp.webp"
    with open(image_path, "rb") as f:
        files = {"image": ("test-webp.webp", f, "image/webp")}
        response = await client.post(
            f"/messaging/images/{conversation_id}/images",
            files=files,
            headers=auth_headers
        )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["image_path"].startswith(f"/{conversation_id}/")

@pytest.mark.asyncio
async def test_upload_png_fails_if_transparent(client, auth_headers, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    """Test upload d'une image PNG qui échoue si elle a de la transparence"""
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    conv_res = await client.post(
        "/messaging/conversations",
        json={"listing_id": str(test_listing_id)},
        headers=auth_headers
    )
    conversation_id = conv_res.json()["id"]
    
    image_path = TEST_IMAGES_DIR / "test-png.png"
    with open(image_path, "rb") as f:
        files = {"image": ("test-png.png", f, "image/png")}
        response = await client.post(
            f"/messaging/images/{conversation_id}/images",
            files=files,
            headers=auth_headers
        )
    
    assert response.status_code == 400
    assert "Transparency is not allowed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_invalid_file_fails(client, auth_headers, test_user_id_1, test_user_id_2, test_listing_id, mock_listing_service):
    """Test upload d'un fichier qui n'est pas une image"""
    mock_listing = MagicMock()
    mock_listing.vendor_id = test_user_id_2
    mock_listing_service.get_by_id = AsyncMock(return_value=mock_listing)
    
    conv_res = await client.post(
        "/messaging/conversations",
        json={"listing_id": str(test_listing_id)},
        headers=auth_headers
    )
    conversation_id = conv_res.json()["id"]
    
    image_path = TEST_IMAGES_DIR / "test-not_an_image.png" # C'est supposé être invalide
    with open(image_path, "rb") as f:
        files = {"image": ("test-not_an_image.png", f, "image/png")}
        response = await client.post(
            f"/messaging/images/{conversation_id}/images",
            files=files,
            headers=auth_headers
        )
    
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]
