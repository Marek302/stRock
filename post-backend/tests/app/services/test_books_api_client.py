import pytest
from unittest.mock import patch, MagicMock
from app.services.books_api_client import fetch_volume_categories

@pytest.fixture
def mock_config():
    with (patch("app.services.books_api_client.BOOKS_API_BASE_URL", "http://books-api"), 
          patch("app.services.books_api_client.BOOKS_API_TIMEOUT", 1.0)):
        yield

def test_fetch_volume_categories_success(mock_config):
    book_id = "test_id"
    categories = ["Fiction", "Magic"]
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"categories": categories}
        mock_client.get.return_value = mock_response
        
        result = fetch_volume_categories(book_id)
        
        assert result == categories
        mock_client.get.assert_called_once_with(f"http://books-api/books/volumes/{book_id}")

def test_fetch_volume_categories_404(mock_config):
    book_id = "unknown_id"
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        result = fetch_volume_categories(book_id)
        
        assert result == []

def test_fetch_volume_categories_error_status(mock_config):
    book_id = "error_id"
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get.return_value = mock_response
        
        result = fetch_volume_categories(book_id)
        
        assert result == []

def test_fetch_volume_categories_exception(mock_config):
    book_id = "exception_id"
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.get.side_effect = Exception("Network error")
        
        result = fetch_volume_categories(book_id)
        
        assert result == []

def test_fetch_volume_categories_no_base_url():
    with patch("app.services.books_api_client.BOOKS_API_BASE_URL", ""):
        result = fetch_volume_categories("some_id")
        assert result == []

def test_fetch_volume_categories_no_book_id(mock_config):
    result = fetch_volume_categories("")
    assert result == []

def test_fetch_volume_categories_invalid_json(mock_config):
    book_id = "invalid_json_id"
    
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not_categories": []}
        mock_client.get.return_value = mock_response
        
        result = fetch_volume_categories(book_id)
        
        assert result == []
