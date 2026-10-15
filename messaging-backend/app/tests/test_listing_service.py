import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from app.services.listing_service import ListingService
from app.models.listing import Listing

@pytest.fixture
def listing_service():
    return ListingService()

async def test_get_by_id_success(listing_service):
    listing_id = uuid4()
    mock_data = {
        "id": str(listing_id),
        "title": "Test Book",
        "vendor_id": "vendor123",
        "book_id": "book123",
        "description": "A test book description",
        "price": 19.99,
        "damage_state": {"id": "1", "name": "New"},
        "sold_state": {"id": "1", "name": "Available"},
        "shipping_offer": {"id": "1", "name": "Standard", "delivery_offer": True},
        "location": "Montreal",
        "seller_rep": 5,
        "is_annoted": False,
        "buyer": None,
        "images": [
            {
                "id": str(uuid4()),
                "image_path": "path/to/image.jpg",
                "image_index": 0,
                "listing_id": str(listing_id)
            }
        ]
    }
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        
        result = await listing_service.get_by_id(listing_id)
        
        assert isinstance(result, Listing)
        assert result.vendor_id == "vendor123"
        assert str(result.id) == str(listing_id)

async def test_get_by_id_partial_images(listing_service):
    listing_id = uuid4()
    # Real data format from user's curl output
    mock_data = {
        "id": str(listing_id),
        "vendor_id": "kvG689qMNVequs7iLjWVIK6RUca2",
        "book_id": "kK8dMQAACAAJ",
        "title": "Calcul 1",
        "damage_state": {"id": "5c8a7b3c-9f13-485d-8b2a-2feed9a8e4a1", "name": "Comme neuf"},
        "sold_state": {"id": "26fbcfa4-e63e-4666-8458-c544dff205c0", "name": "Not Sold"},
        "description": "Livre de calcul différentiel et intégral en excellent état.",
        "price": 45.99,
        "shipping_offer": {"id": "1345bd31-fff5-489f-af26-1046f961a2ee", "name": "Ship", "delivery_offer": True},
        "location": "Montréal",
        "is_annoted": False,
        "seller_rep": 5,
        "buyer": None,
        "images": [
            {
                "id": "516f02b6-52c4-4e48-8e4f-5ddee3024878",
                "image_index": 0,
                "listing_id": str(listing_id)
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
        
        assert isinstance(result, Listing)
        assert len(result.images) == 1
        assert result.images[0].image_path is None
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
