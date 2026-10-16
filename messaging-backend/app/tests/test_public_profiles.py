import unittest
from unittest.mock import AsyncMock, MagicMock
from app.services.messaging_repo import MongoMessagingRepository


class PublicProfileTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.profiles = AsyncMock()
        self.conversations = AsyncMock()
        db = MagicMock()
        db.__getitem__.side_effect = lambda name: self.profiles if name == 'public_profiles' else self.conversations
        self.repo = MongoMessagingRepository(db)

    async def test_verified_display_fields_are_saved_without_email(self):
        profile = await self.repo.save_public_profile('alice', 'Alice', 'https://example.test/alice.png')
        self.assertEqual(profile, {'uid': 'alice', 'displayName': 'Alice', 'photoURL': 'https://example.test/alice.png'})
        self.profiles.update_one.assert_awaited_once_with({'_id': 'alice'}, {'$set': profile}, upsert=True)

    async def test_contact_can_read_shared_profile(self):
        self.conversations.find_one.return_value = {'participants': ['alice', 'bob']}
        self.profiles.find_one.return_value = {'uid': 'bob', 'displayName': 'Bob', 'photoURL': ''}
        result = await self.repo.get_contact_profile('alice', 'bob')
        self.assertEqual(result['displayName'], 'Bob')
        self.conversations.find_one.assert_awaited_once_with({'participants': {'$all': ['alice', 'bob']}})

    async def test_outsider_cannot_read_profile(self):
        self.conversations.find_one.return_value = None
        with self.assertRaises(PermissionError):
            await self.repo.get_contact_profile('outsider', 'bob')
        self.profiles.find_one.assert_not_awaited()
