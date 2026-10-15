import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.messaging_service import MessagingService
from app.schemas.conversation import Conversation
from uuid import uuid4
from datetime import datetime

@pytest.mark.asyncio
async def test_get_message_by_listing_and_participant_success():
    # Mock data
    buyer_id = "u" * 28
    encoded_token = "fake-token"
    listing_id = uuid4()
    conversation_id = uuid4()
    
    mock_response_data = {
        "id": str(conversation_id),
        "participants": [buyer_id, "v" * 28],
        "listing_id": str(listing_id),
        "created_at": datetime.now().isoformat(),
        "last_message": {
            "content": "Hello",
            "sender_uid": buyer_id,
            "timestamp": datetime.now().isoformat()
        },
        "other_participant_firebase_uid": "v" * 28
    }

    service = MessagingService()
    
    with patch("httpx.AsyncClient.__aenter__", return_value=AsyncMock()) as mock_aenter:
        mock_client = mock_aenter.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        
        result = await service.get_message_by_listing_and_participant(
            buyer_id=buyer_id,
            encoded_token=encoded_token,
            listing_id=listing_id
        )
        
        assert isinstance(result, Conversation)
        assert result.id == conversation_id
        assert result.listing_id == listing_id
        
        mock_client.get.assert_called_once_with(
            url=f"http://messaging-api:8000/messaging/conversations/by-listing-and-participant?listing_id={listing_id}&buyer_id={buyer_id}",
            headers={"Authorization": f"Bearer {encoded_token}"}
        )

@pytest.mark.asyncio
async def test_get_message_by_listing_and_participant_failure():
    buyer_id = "u" * 28
    encoded_token = "fake-token"
    listing_id = uuid4()
    
    service = MessagingService()
    
    with patch("httpx.AsyncClient.__aenter__", return_value=AsyncMock()) as mock_aenter:
        mock_client = mock_aenter.return_value
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_client.get.return_value = mock_response
        
        with pytest.raises(Exception, match="Not Found"):
            await service.get_message_by_listing_and_participant(
                buyer_id=buyer_id,
                encoded_token=encoded_token,
                listing_id=listing_id
            )

@pytest.mark.asyncio
async def test_get_messaging_service():
    service = await MessagingService.get_messaging_service()
    assert isinstance(service, MessagingService)
