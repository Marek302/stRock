"""Access for Firebase users without legacy custom permission claims."""
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.api.routes import router
from app.models.messaging import Conversation
from app.services.firebase_token_service import get_firebase_token_service
from app.services.messaging_service import MessagingService
from app.services.listing_service import ListingService


class ConnectedUserAccessTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix='/messaging')
        self.token = SimpleNamespace(uid='connected-user', permissions=[])
        self.verifier = SimpleNamespace(verify_id_token=AsyncMock(return_value=self.token))
        self.app.dependency_overrides[get_firebase_token_service] = lambda: self.verifier
        self.repo = AsyncMock()
        self.repo.list_conversations_for_user.return_value = []
        self.repo.list_messages.return_value = []
        self.conversation = Conversation(
            id=uuid4(), listing_id=uuid4(), participants=['connected-user', 'strock-demo-alice'],
            created_at=datetime.now(timezone.utc),
        )
        self.repo.get_conversation.return_value = self.conversation
        self.app.state.messaging_service = MessagingService(self.repo, AsyncMock())
        self.client = TestClient(self.app)
        self.headers = {'Authorization': 'Bearer verified-by-mock'}

    def test_connected_user_needs_no_custom_claims(self):
        response = self.client.get('/messaging/conversations', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.repo.list_conversations_for_user.assert_awaited_once_with('connected-user')

    def test_create_conversation_without_custom_claims(self):
        listing = SimpleNamespace(user_id='strock-demo-alice')
        listings = SimpleNamespace(get_by_id=AsyncMock(return_value=listing))
        self.app.dependency_overrides[ListingService.get_listing_service] = lambda: listings
        self.repo.find_conversation_by_pair_listing.return_value = None
        response = self.client.post('/messaging/conversations', headers=self.headers,
                                    json={'listing_id': str(self.conversation.listing_id)})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(set(response.json()['participants']), {'connected-user', 'strock-demo-alice'})
        self.repo.insert_conversation.assert_awaited_once()

    def test_member_can_read_messages(self):
        response = self.client.get(f'/messaging/conversations/{self.conversation.id}/messages', headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_read_messages(self):
        self.token.uid = 'outsider'
        response = self.client.get(f'/messaging/conversations/{self.conversation.id}/messages', headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.repo.list_messages.assert_not_awaited()

    def test_missing_token_is_rejected(self):
        response = self.client.get('/messaging/conversations')
        self.assertIn(response.status_code, [401, 403])
        self.repo.list_conversations_for_user.assert_not_awaited()

    def test_invalid_token_is_rejected(self):
        self.verifier.verify_id_token.side_effect = HTTPException(status_code=401)
        response = self.client.get('/messaging/conversations', headers=self.headers)
        self.assertEqual(response.status_code, 401)
        self.repo.list_conversations_for_user.assert_not_awaited()
