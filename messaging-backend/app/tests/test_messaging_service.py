"""
Tests unitaires pour le MessagingService.
Tests de la logique métier isolée du repository.
"""
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
import random
import string
import asyncio
from unittest.mock import MagicMock
import pytest


from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.services.messaging_service import MessagingService
from app.models.messaging import Conversation, Message, LastMessage


# Création de faux repository par Goypilot - Justin 


class FakeMessagingRepository:
    """Faux repository pour les tests unitaires"""
    
    def __init__(self):
        self.conversations = {}
        self.messages = {}
        self.pair_listing_index = {}
    
    async def find_conversation_by_pair_listing(
        self,
        pair_key: str,
        listing_id: UUID,
    ) -> Optional[Conversation]:
        key = f"{pair_key}|{listing_id}"
        conv_id = self.pair_listing_index.get(key)
        if conv_id:
            return self.conversations.get(conv_id)
        return None
    
    async def insert_conversation(
        self,
        conversation: Conversation,
        pair_key: str,
    ) -> None:
        key = f"{pair_key}|{conversation.listing_id}"
        if key in self.pair_listing_index:
            raise ConflictError("Conversation already exists")
        
        self.conversations[conversation.id] = conversation
        self.pair_listing_index[key] = conversation.id
    
    async def list_conversations_for_user(
        self,
        user_id: UUID,
    ) -> List[Conversation]:
        result = []
        for conv in self.conversations.values():
            if str(user_id) in conv.participants:
                result.append(conv)
        
        # Trier par last_message timestamp (plus récent en premier)
        result.sort(
            key=lambda c: c.last_message.timestamp if c.last_message else c.created_at,
            reverse=True
        )
        return result
    
    async def get_conversations_by_listing_id(
        self,
        listing_id: UUID,
    ) -> List[Conversation]:
        return [
            conv for conv in self.conversations.values()
            if conv.listing_id == listing_id
        ]
    
    async def get_conversation(
        self,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        return self.conversations.get(conversation_id)
    
    async def list_messages(
        self,
        conversation_id: UUID,
    ) -> List[Message]:
        return [
            msg for msg in self.messages.values()
            if msg.conversation_id == conversation_id
        ]
    
    async def insert_message(
        self,
        message: Message,
    ) -> None:
        self.messages[message.id] = message
    
    async def set_conversation_last_message(
        self,
        conversation_id: UUID,
        last_message: LastMessage,
    ) -> None:
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.last_message = last_message
    
    async def mark_messages_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> int:
        count = 0
        for msg in self.messages.values():
            if msg.conversation_id == conversation_id and user_id not in msg.read_by:
                msg.read_by.append(user_id)
                count += 1
        return count

    async def delete_message_by_id(self, message_id: UUID) -> None:
        if message_id in self.messages:
            del self.messages[message_id]

    async def delete_conversation(self, conversation_id: UUID) -> None:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        # Suppression des messages associés
        to_delete = [mid for mid, msg in self.messages.items() if msg.conversation_id == conversation_id]
        for mid in to_delete:
            del self.messages[mid]

    async def delete_conversations_by_listing_id(self, listing_id: UUID, participant_uid: str) -> None:
        to_delete_convs = []
        for conv_id, conv in self.conversations.items():
            if conv.listing_id == listing_id and participant_uid in conv.participants:
                to_delete_convs.append(conv_id)
                
        for conv_id in to_delete_convs:
            await self.delete_conversation(conv_id)


class FakeImageService:
    """Faux service d'images pour les tests unitaires"""
    def __init__(self):
        self.images = {}

    async def get_by_id(self, image_id: UUID) -> object:
        if image_id not in self.images:
            raise Exception("Image not found")
        return self.images[image_id]

@pytest.fixture
def repo():
    """Fixture pour le repository fake"""
    return FakeMessagingRepository()

@pytest.fixture
def image_service():
    """Fixture pour le service d'images fake"""
    return FakeImageService()

@pytest.fixture
def service(repo, image_service):
    """Fixture pour le service de messagerie"""
    return MessagingService(repo, image_service)


@pytest.fixture
def user1_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def user2_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))


@pytest.fixture
def listing_id():
    return uuid4()


class TestGetConversationByParticipants:
    """Tests pour la récupération de conversations."""

    def test_get_existing_conversation(self, service, user1_id, user2_id, listing_id):
        """Test récupération conversation existante"""
        async def run():
            created_convo = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )
            fetched_convo = await service.get_conversation_by_participants(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
            )
            return created_convo, fetched_convo

        created_convo, fetched_convo = asyncio.run(run())
        assert fetched_convo is not None
        assert created_convo.id == fetched_convo.id

    def test_get_non_existent_conversation(self, service, user1_id, user2_id, listing_id):
        """Test récupération conversation n'exsite pas"""
        async def run():
            return await service.get_conversation_by_participants(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
            )

        conversation = asyncio.run(run())
        assert conversation is None

    def test_participant_order_does_not_matter(self, service, user1_id, user2_id, listing_id):
        """Test that participant order does not matter for retrieval."""
        async def run():
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )
            convo1 = await service.get_conversation_by_participants(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
            )
            convo2 = await service.get_conversation_by_participants(
                participants=[user2_id, user1_id],
                listing_id=listing_id,
            )
            return convo1, convo2

        convo1, convo2 = asyncio.run(run())
        assert convo1 is not None
        assert convo2 is not None
        assert convo1.id == convo2.id


class TestCreateConversation:
    """Tests pour la création de conversations"""

    def test_create_new_conversation(self, service, user1_id, user2_id, listing_id):
        """Test création d'une nouvelle conversation"""
        async def run():
            return await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
                caller_firebase_uid="a" * 28
            )

        conversation = asyncio.run(run())
        assert conversation.id is not None
        assert set(conversation.participants) == {user1_id, user2_id}
        assert conversation.listing_id == listing_id
        assert conversation.last_message is None
        assert isinstance(conversation.created_at, datetime)
        assert conversation.participant_firebase_uids == {user1_id: "a" * 28}

    def test_create_conversation_fails_if_exists(self, service, user1_id, user2_id, listing_id):
        """Test création d'une conversation qui existe déjà"""
        async def run():
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )

        with pytest.raises(ConflictError):
            asyncio.run(run())

    def test_create_conversation_fails_if_exists_reversed_participants(self, service, user1_id, user2_id, listing_id):
        """Test création d'une conversation qui existe déjà avec participants inversés"""
        async def run():
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )
            await service.create_conversation(
                participants=[user2_id, user1_id],
                listing_id=listing_id,
                caller_uid=user2_id,
            )

        with pytest.raises(ConflictError):
            asyncio.run(run())

    def test_different_listings_different_conversations(self, service, user1_id, user2_id):
        """Test différents listings créés différentes conversations"""
        listing1 = uuid4()
        listing2 = uuid4()
        async def run():
            conv1 = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing1,
                caller_uid=user1_id
            )
            conv2 = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing2,
                caller_uid=user1_id
            )
            return conv1, conv2

        conv1, conv2 = asyncio.run(run())
        assert conv1.id != conv2.id

    def test_invalid_participants_count(self, service, user1_id):
        """Test création avec nombre de participants invalides"""
        listing_id = uuid4()
        with pytest.raises(ValueError, match="deux participants"):
            asyncio.run(service.create_conversation(
                participants=[user1_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            ))


class TestGetMessages:
    """Tests pour la récupération des messages"""
    
    def test_get_messages_empty(self, service, user1_id, user2_id, listing_id):
        """Test de récupération sans messages"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id,
            )
            messages = await service.get_messages(conversation.id, user1_id)
            return messages

        messages = asyncio.run(run())
        assert messages == []
    
    def test_get_messages_nonexistent_conversation(self, service, user1_id):
        """Test avec une conversation inexistante"""
        fake_id = uuid4()
        with pytest.raises(NotFoundError, match="introuvable"):
            asyncio.run(service.get_messages(fake_id, user1_id))
    
    def test_get_messages_unauthorized(self, service, user1_id, user2_id, listing_id):
        """Test d'accès non autorisé"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            user3_id = "".join(random.choices(string.ascii_letters + string.digits, k=28))
            await service.get_messages(conversation.id, user3_id)

        with pytest.raises(ForbiddenError, match="Acces refuse"):
            asyncio.run(run())


class TestSendMessage:
    """Tests pour l'envoi de messages"""
    
    def test_send_message(self, service, repo, user1_id, user2_id, listing_id):
        """Test d'envoi d'un message"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            message = await service.send_message(
                conversation.id,
                user1_id,
                "Bonjour! Le livre est-il disponible?"
            )
            messages = await repo.list_messages(conversation.id)
            return message, messages, conversation.id

        message, messages, conversation_id = asyncio.run(run())

        assert message.id is not None
        assert message.conversation_id == conversation_id
        assert message.sender_uid == user1_id
        assert message.content == "Bonjour! Le livre est-il disponible?"
        assert isinstance(message.timestamp, datetime)
        assert user1_id in message.read_by
        assert len(messages) == 1
    
    def test_send_message_updates_last_message(self, service, repo, user1_id, user2_id, listing_id):
        """Test que l'envoi met à jour last_message"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            await service.send_message(
                conversation.id,
                user1_id,
                "Premier message"
            )
            return await repo.get_conversation(conversation.id)

        updated_conv = asyncio.run(run())
        assert updated_conv.last_message is not None
        assert updated_conv.last_message.content == "Premier message"
        assert updated_conv.last_message.sender_uid == user1_id

    def test_send_message_with_images(self, service, repo, image_service, user1_id, user2_id, listing_id):
        """Test d'envoi d'un message avec des images"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            image_ids = [uuid4(), uuid4()]
            for img_id in image_ids:
                image_service.images[img_id] = MagicMock()
                
            message = await service.send_message(
                conversation.id,
                user1_id,
                "Voici des images",
                image_ids=image_ids
            )
            return message

        message = asyncio.run(run())
        assert message.image_ids is not None
        assert len(message.image_ids) == 2
        assert message.content == "Voici des images"

    def test_send_message_with_images_only(self, service, repo, image_service, user1_id, user2_id, listing_id):
        """Test d'envoi d'un message avec seulement des images"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            image_ids = [uuid4()]
            for img_id in image_ids:
                image_service.images[img_id] = MagicMock()

            message = await service.send_message(
                conversation.id,
                user1_id,
                "", 
                image_ids=image_ids
            )
            updated_conv = await repo.get_conversation(conversation.id)
            return message, updated_conv

        message, updated_conv = asyncio.run(run())
        assert message.image_ids is not None
        assert len(message.image_ids) == 1
        assert message.content == ""
        assert updated_conv.last_message.content == "Image"

    def test_send_empty_message_fails(self, service, user1_id, user2_id, listing_id):
        """Test que l'envoi d'un message sans contenu ni images échoue"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            await service.send_message(
                conversation.id,
                user1_id,
                "", 
                image_ids=None 
            )

        with pytest.raises(ValueError, match="Message must have either content or images"):
            asyncio.run(run())

    def test_send_message_invalid_image_fails(self, service, user1_id, user2_id, listing_id):
        """Test que l'envoi d'un message avec une image inexistante échoue"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            await service.send_message(
                conversation.id,
                user1_id,
                "Look at this beautiful image my friend.",
                image_ids=[uuid4()]
            )

        with pytest.raises(NotFoundError, match="Image with id"):
            asyncio.run(run())


class TestDelete:
    """Tests pour la suppression de conversations et messages"""

    def test_delete_conversation_success(self, service, repo, user1_id, user2_id, listing_id):
        """Test de suppression réussie d'une conversation"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            await service.send_message(conversation.id, user1_id, "Hello")
            
            # Vérifier que ça existe
            assert await repo.get_conversation(conversation.id) is not None
            assert len(await repo.list_messages(conversation.id)) == 1
            
            # Supprimer
            await service.delete_conversation(conversation.id, user1_id)
            
            # Vérifier que c'est supprimé
            assert await repo.get_conversation(conversation.id) is None
            assert len(await repo.list_messages(conversation.id)) == 0

        asyncio.run(run())

    def test_delete_conversation_unauthorized(self, service, user1_id, user2_id, listing_id):
        """Test de suppression de conversation par un non-membre"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            user3_id = "someone_else"
            await service.delete_conversation(conversation.id, user3_id)

        with pytest.raises(ForbiddenError):
            asyncio.run(run())

    def test_delete_message_success(self, service, repo, user1_id, user2_id, listing_id):
        """Test de suppression réussie d'un message"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            message = await service.send_message(conversation.id, user1_id, "To be deleted")
            
            # Supprimer
            await service.delete_message_by_id(conversation.id, message.id, user1_id)
            
            # Vérifier
            messages = await repo.list_messages(conversation.id)
            assert len(messages) == 0

        asyncio.run(run())

    def test_delete_message_unauthorized(self, service, user1_id, user2_id, listing_id):
        """Test de suppression de message par un non-membre"""
        async def run():
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            message = await service.send_message(conversation.id, user1_id, "Safe message")
            user3_id = "someone_else"
            await service.delete_message_by_id(conversation.id, message.id, user3_id)

        with pytest.raises(ForbiddenError):
            asyncio.run(run())


class TestEnsureConversationMemberByListingId:
    """Tests pour ensure_conversations_member_by_listing_id"""

    def test_existing_member(self, service, user1_id, user2_id, listing_id):
        """Test pour un membre existant dans la conversation"""
        async def run():
            conversation: Conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            fetched: List[Conversation] = await service.ensure_conversations_member_by_listing_id(listing_id, user1_id)
           
            return conversation, fetched

        conversation, fetched = asyncio.run(run())
        assert fetched is not None
        assert fetched[0].id == conversation.id

    def test_not_a_member(self, service, user1_id, user2_id, listing_id):
        """Test pour un utilisateur non membre de la conversation"""
        async def run():
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            user3_id = "someone_else"
            await service.ensure_conversations_member_by_listing_id(listing_id, user3_id)

        with pytest.raises(ForbiddenError, match="Acces refuse a cette conversation."):
            asyncio.run(run())


class TestDeleteConversationByListingId:
    """Tests pour delete_conversations_by_listing_id"""

    def test_delete_success(self, service, repo, user1_id, user2_id, listing_id):
        """Test de suppression réussie de toutes les conversations d'un listing"""
        async def run():
            # Créer une conversation
            conversation = await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            await service.send_message(conversation.id, user1_id, "Message test")
            
            # Vérifier qu'elle existe
            assert len(await repo.get_conversations_by_listing_id(listing_id)) == 1
            
            # Supprimer
            await service.delete_conversations_by_listing_id(listing_id, user1_id)
            
            # Vérifier que c'est supprimé (ainsi que les messages)
            assert len(await repo.get_conversations_by_listing_id(listing_id)) == 0
            assert len(await repo.list_messages(conversation.id)) == 0

        asyncio.run(run())

    def test_delete_unauthorized(self, service, user1_id, user2_id, listing_id):
        """Test de suppression refusée pour un non-membre"""
        async def run():
            await service.create_conversation(
                participants=[user1_id, user2_id],
                listing_id=listing_id,
                caller_uid=user1_id
            )
            user3_id = "someone_else"
            await service.delete_conversations_by_listing_id(listing_id, user3_id)
        with pytest.raises((ForbiddenError, NotFoundError)):
            asyncio.run(run())

    def test_delete_no_conversations(self, service, user1_id):
        """Test de suppression quand il n'y a aucune conversation pour le listing"""
        async def run():
            non_existent_listing = uuid4()
            await service.delete_conversations_by_listing_id(non_existent_listing, user1_id)

        asyncio.run(run())

