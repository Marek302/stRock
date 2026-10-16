
from datetime import datetime, timezone
import logging
from typing import List, Optional, Protocol, Tuple
from uuid import UUID, uuid4

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.messaging import Conversation, LastMessage, Message


# ===== Repository contract =====

class ImageServiceProtocol(Protocol):
    async def get_by_id(self, image_id: UUID) -> object:
        ...


class NotificationServiceProtocol(Protocol):
    async def send_new_message_notification(
        self,
        receiver_uid: str,
        sender_uid: str,
        conversation_id: UUID,
        content: str,
        sender_name: Optional[str] = None,
        article_title: Optional[str] = None,
    ) -> None:
        ...

class MessagingRepository(Protocol):

    async def find_conversation_by_pair_listing(
        self,
        pair_key: str,
        listing_id: UUID,
    ) -> Optional[Conversation]:
        ...

    async def insert_conversation(
        self,
        conversation: Conversation,
        pair_key: str,
    ) -> None:
        ...

    async def list_conversations_for_user(
        self,
        user_id: str,
    ) -> List[Conversation]:
        ...

    async def get_conversation(
        self,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        ...

    async def list_messages(
        self,
        conversation_id: UUID,
    ) -> List[Message]:
        ...

    async def insert_message(
        self,
        message: Message,
    ) -> None:
        ...

    async def set_conversation_last_message(
        self,
        conversation_id: UUID,
        last_message: LastMessage,
    ) -> None:
        ...

    async def mark_messages_read(
        self,
        conversation_id: UUID,
        user_id: str,
    ) -> int:
        ...

    async def get_by_listing_and_participants(
        self,
        listing_id : UUID,
        participants: List[str]
    ) -> Optional[Conversation]:
        ...
    async def delete_message_by_id(self, message_id: UUID) -> None:
        ...
    async def delete_conversation(self, conversation_id: UUID) -> None:
        ...          
    async def get_conversations_by_listing_id(
        self, 
        listing_id: UUID
        ) -> Optional[List[Conversation]]:
        ...                      

# ===== Helpers =====

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def canonical_pair_key(participants: List[str], listing_id: UUID) -> Tuple[str, str, str]:
    """
    Returns:
      - user1, user2 (stable ordering)
      - pair_key: "user1|user2|listing_id"
    """
    if len(participants) != 2:
        raise ValueError("Il ne peut y avoir que deux participants.")

    a, b = participants
    user1, user2 = (a, b) if str(a) < str(b) else (b, a)
    pair_key = f"{user1}|{user2}|{listing_id}"

    return user1, user2, pair_key


# ===== Service =====

logger = logging.getLogger(__name__)


class NullNotificationService:
    async def send_new_message_notification(
        self,
        receiver_uid: str,
        sender_uid: str,
        conversation_id: UUID,
        content: str,
        sender_name: Optional[str] = None,
        article_title: Optional[str] = None,
    ) -> None:
        return None

class MessagingService:

    def __init__(
        self,
        repo: MessagingRepository,
        image_service: ImageServiceProtocol,
        notification_service: Optional[NotificationServiceProtocol] = None,
    ):
        self.repo = repo
        self.image_service = image_service
        self.notification_service = notification_service or NullNotificationService()

    async def get_conversation_by_listing_and_participants(
        self,
        listing_id: UUID,
        participants: List[str],
        ) -> Conversation:
        convo = await self.repo.get_by_listing_id_and_participant(
            listing_id, participants
        )
        if not convo:
            raise NotFoundError("Conversation was not found.")
        
        return convo

    async def get_conversation_by_participants(
        self,
        participants: List[str],
        listing_id: UUID,
    ) -> Optional[Conversation]:
        """
        Recherche une conversation par les participants et l'ID de l'annonce.
        """
        _, _, pair_key = canonical_pair_key(participants, listing_id)
        return await self.repo.find_conversation_by_pair_listing(
            pair_key, listing_id
        )

    async def create_conversation(
        self,
        participants: List[str],
        listing_id: UUID,
        *,
        caller_uid: str,
        caller_firebase_uid: Optional[str] = None,
    ) -> Conversation:
        """
        Crée une nouvelle conversation.
        Cette méthode lèvera une ConflictError si une conversation pour ces participants
        et cette annonce existe déjà.
        """
        user1, user2, pair_key = canonical_pair_key(participants, listing_id)

        # Vérifier si une conversation existe déjà
        existing = await self.repo.find_conversation_by_pair_listing(pair_key, listing_id)
        if existing:
            raise ConflictError("Conversation already exists")

        participant_firebase_uids = None
        if caller_uid and caller_firebase_uid and 1 <= len(caller_firebase_uid) <= 128:
            participant_firebase_uids = {str(caller_uid): caller_firebase_uid}

        convo = Conversation(
            id=uuid4(),
            participants=[user1, user2],
            listing_id=listing_id,
            created_at=_now_utc(),
            last_message=None,
            participant_firebase_uids=participant_firebase_uids,
        )

        await self.repo.insert_conversation(convo, pair_key)
        return convo

    async def ensure_conversations_member_by_listing_id(
        self,
        listing_id: UUID,
        user_id: str,
    ) -> Optional[List[Conversation]]:
        conversations = await self.repo.get_conversations_by_listing_id(listing_id)
        for convo in conversations:
            await self.ensure_conversation_member(convo.id, user_id)
        return conversations
    
    async def delete_conversations_by_listing_id(self, listing_id: UUID, participant_uid: str) -> None:
        conversation = await self.ensure_conversations_member_by_listing_id(listing_id, participant_uid)
        for convo in conversation:
            await self.delete_conversation(convo.id, participant_uid)

    async def delete_conversation(self, conversation_id: UUID, participant_uid: str) -> None:
        await self.ensure_conversation_member(conversation_id, participant_uid)
        await self.repo.delete_conversation(conversation_id)


    async def delete_message_by_id(self, conversation_id: UUID, message_id: UUID, participant_uid: str) -> None:
        await self.ensure_conversation_member(conversation_id=conversation_id, user_id=participant_uid)
        await self.repo.delete_message_by_id(message_id)

    async def list_user_conversations(
        self,
        user_id: str,
    ) -> List[Conversation]:
        return await self.repo.list_conversations_for_user(user_id)

  

    async def ensure_conversation_member(
        self,
        conversation_id: UUID,
        user_id: str,
    ) -> Conversation:
        convo = await self.repo.get_conversation(conversation_id)
        if not convo:
            raise NotFoundError("Conversation introuvable.")
        if user_id not in convo.participants:
            raise ForbiddenError("Acces refuse a cette conversation.")
        return convo

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: str,
    ) -> List[Message]:
        await self.ensure_conversation_member(conversation_id, user_id)
        return await self.repo.list_messages(conversation_id)

    async def send_message(
        self,
        conversation_id: UUID,
        sender_uid: str,
        content: str,
        image_ids: Optional[List[UUID]] = None,
        sender_name: Optional[str] = None,
        article_title: Optional[str] = None,
    ) -> Message:

        cleaned = content.strip()
        if not cleaned and not image_ids:
            raise ValueError("Message must have either content or images")

        convo = await self.repo.get_conversation(conversation_id)
        if not convo:
            raise NotFoundError("Conversation was not found.")

        if sender_uid not in convo.participants:
            raise ForbiddenError("Access to this conversation has been denied.")

        if image_ids:
            for image_id in image_ids:
                try:
                    await self.image_service.get_by_id(image_id)
                except Exception as exc:
                    raise NotFoundError(f"Image with id: {image_id} was not found") from exc

        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_uid=sender_uid,
            content=cleaned,
            image_ids=image_ids,
            timestamp=_now_utc(),
            read_by=[sender_uid],
        )

        await self.repo.insert_message(message)

        last_message_content = cleaned[:32] if cleaned else "Image"
        last_message = LastMessage(
            content=last_message_content,
            sender_uid=sender_uid,
            timestamp=message.timestamp,
        )
        await self.repo.set_conversation_last_message(conversation_id, last_message)

        receiver_uid = next((participant for participant in convo.participants if participant != sender_uid), None)
        if receiver_uid:
            try:
                await self.notification_service.send_new_message_notification(
                    receiver_uid=receiver_uid,
                    sender_uid=sender_uid,
                    conversation_id=conversation_id,
                    content=cleaned,
                    sender_name=sender_name,
                    article_title=article_title,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to send push notification for conversation %s: %s",
                    conversation_id,
                    exc,
                )

        return message

    async def mark_conversation_as_read(
        self,
        conversation_id: UUID,
        user_id: str,
    ) -> int:

        convo = await self.repo.get_conversation(conversation_id)
        if not convo:
            raise NotFoundError("Conversation was not found.")

        if user_id not in convo.participants:
            raise ForbiddenError("Access to this conversation has been denied.")

        return await self.repo.mark_messages_read(conversation_id, user_id)
