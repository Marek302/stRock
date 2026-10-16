import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from app.services.listing_service import ListingService
from app.models.listing import Post

@pytest.fixture
def listing_service():
    return ListingService()

async def test_get_by_id_success(listing_service):
    listing_id = uuid4()
    mock_data = {
        "id": str(listing_id),
        "title": "Test Book",
        "created_at": "2026-10-16T12:00:00Z",
        "user_id": "vendor123",
        "description": "A test book description",
        "location": "Montreal",
        "images": [
            {
                "id": str(uuid4()),
                "image_index": 0,
                "post_id": str(listing_id)
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        result = await listing_service.get_by_id(listing_id)
        
        mock_get.assert_awaited_once_with(f"http://post-backend:8000/api/v1/posts/{listing_id}")
        assert isinstance(result, Post)
        assert result.user_id == "vendor123"
        assert str(result.id) == str(listing_id)

async def test_get_by_id_partial_images(listing_service):
    listing_id = uuid4()
    mock_data = {
        "id": str(listing_id),
        "user_id": "kvG689qMNVequs7iLjWVIK6RUca2",
        "title": "Calcul 1",
        "created_at": "2026-10-16T12:00:00Z",
        "description": "Livre de calcul différentiel et intégral en excellent état.",
        "location": "Montréal",
        "images": [
            {
                "id": "516f02b6-52c4-4e48-8e4f-5ddee3024878",
                "image_index": 0,
                "post_id": str(listing_id)
            }
        ],
        "extra_field_from_api": "should be ignored"
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        result = await listing_service.get_by_id(listing_id)
        
        assert isinstance(result, Post)
        assert len(result.images) == 1
        assert result.images[0].post_id == listing_id
        assert result.images[0].image_index == 0
        assert result.title == "Calcul 1"

async def test_get_by_id_not_found(listing_service):
    listing_id = uuid4()
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = await listing_service.get_by_id(listing_id)
        
        assert result is None

async def test_get_by_id_error(listing_service):
    listing_id = uuid4()
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception):
            await listing_service.get_by_id(listing_id)

def test_get_listing_service():
    service = ListingService.get_listing_service()
    assert isinstance(service, ListingService)

@pytest.mark.parametrize("user_id", [None, "", "u" * 129])
def test_post_requires_valid_author(user_id):
    from pydantic import ValidationError

    data = {
        "id": str(uuid4()), "title": "Publication", "description": "Bonjour",
        "created_at": "2026-10-16T12:00:00Z",
    }
    if user_id is not None:
        data["user_id"] = user_id
    with pytest.raises(ValidationError):
        Post.model_validate(data)


def test_event_fields_match_publication_response():
    post = Post.model_validate({
        "id": str(uuid4()), "user_id": "author123", "title": "Rencontre",
        "description": "Rencontre du quartier", "content_type": "event",
        "latitude": 46.81, "longitude": -71.22, "location": "Saint-Roch",
        "created_at": "2026-10-16T12:00:00Z",
        "starts_at": "2026-10-17T12:00:00Z", "ends_at": "2026-10-17T14:00:00Z",
        "expires_at": "2026-10-17T14:00:00Z", "closed_at": None,
    })
    assert post.user_id == "author123"
    assert post.content_type == "event"
    assert post.starts_at < post.ends_at
    assert post.images == []
