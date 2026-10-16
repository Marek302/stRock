# app/db/repositories/messaging_repo.py

from typing import Any, Dict, List, Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.models.messaging import Conversation, LastMessage, Message
from app.core.exceptions import ConflictError


def _uuid_to_str(value: UUID) -> str:
    return str(value)


def _str_to_uuid(value: str) -> UUID:
    return UUID(value)


def doc_to_conversation(doc: Dict[str, Any]) -> Conversation:
    last = doc.get("last_message")
    last_message: Optional[LastMessage] = None

    if isinstance(last, dict):
        # Accepter sender_uid ou sender_id (rétrocompat)
        sender_uid = last.get("sender_uid") or last.get("sender_id")
        timestamp = last.get("timestamp")
        if sender_uid and timestamp:
            last_message = LastMessage(
                content=str(last.get("content", ""))[:32],
                sender_uid=sender_uid,
                timestamp=timestamp,
            )

    participant_firebase_uids = doc.get("participant_firebase_uids")
    if isinstance(participant_firebase_uids, dict):
        participant_firebase_uids = {k: str(v) for k, v in participant_firebase_uids.items()}
    else:
        participant_firebase_uids = None

    return Conversation(
        id=_str_to_uuid(doc["_id"]),
        participants=(doc["participants"]),
        listing_id=_str_to_uuid(doc["listing_id"]),
        created_at=doc["created_at"],
        last_message=last_message,
        participant_firebase_uids=participant_firebase_uids,
    )


def _doc_to_message(doc: Dict[str, Any]) -> Message:
    image_ids = doc.get("image_ids")
    if image_ids:
        image_ids = [_str_to_uuid(i) for i in image_ids]
    
    return Message(
        id=_str_to_uuid(doc["_id"]),
        conversation_id=_str_to_uuid(doc["conversation_id"]),
        sender_uid=doc["sender_uid"],
        content=doc["content"],
        image_ids=image_ids,
        timestamp=doc["timestamp"],
        read_by=doc.get("read_by", []),
    )

def conversation_to_doc(conversation: Conversation, pair_key: str):
        return {
            "_id": _uuid_to_str(conversation.id),
            "participants": conversation.participants,
            "listing_id": _uuid_to_str(conversation.listing_id),
            "pair_key": pair_key,
            "created_at": conversation.created_at,
            "last_message": None,
        }

class MongoMessagingRepository:
    """
    Mongo implementation of MessagingRepository (Motor async).

    Storage conventions:
      - All UUIDs are stored as strings in Mongo (simple interop with other services).
      - Conversation uniqueness enforced by index on (pair_key, listing_id).
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        conversations_collection: str = "conversations",
        messages_collection: str = "messages",
    ):
        self._db = db
        self._conversations = db[conversations_collection]
        self._messages = db[messages_collection]

    async def save_public_profile(self, uid: str, name: str | None, photo: str | None):
        # Identity and display fields come only from a verified Firebase token.
        profile = {"uid": uid, "displayName": name or "Utilisateur", "photoURL": photo or ""}
        await self._db["public_profiles"].update_one({"_id": uid}, {"$set": profile}, upsert=True)
        return profile

    async def get_contact_profile(self, caller_uid: str, uid: str):
        if caller_uid != uid:
            shared = await self._conversations.find_one({"participants": {"$all": [caller_uid, uid]}})
            if not shared:
                raise PermissionError("Ce profil est réservé aux participants de la conversation.")
        return await self._db["public_profiles"].find_one({"_id": uid}, {"_id": 0})

    async def ensure_indexes(self) -> None:
        """
        Call once on startup.
        Enforces uniqueness and improves performance for common queries.
        """
        await self._conversations.create_index(
            [("pair_key", ASCENDING), ("listing_id", ASCENDING)],
            unique=True,
            name="uniq_pair_listing",
        )

        await self._conversations.create_index(
            [("participants", ASCENDING)],
            name="idx_participants",
        )

        await self._conversations.create_index(
            [("last_message.timestamp", DESCENDING), ("created_at", DESCENDING)],
            name="idx_last_message_sort",
        )

        await self._messages.create_index(
            [("conversation_id", ASCENDING), ("timestamp", ASCENDING)],
            name="idx_conversation_timestamp",
        )

    async def find_conversation_by_pair_listing(
        self,
        pair_key: str,
        listing_id: UUID,
    ) -> Optional[Conversation]:
        doc = await self._conversations.find_one(
            {"pair_key": pair_key, "listing_id": _uuid_to_str(listing_id)}
        )
        return doc_to_conversation(doc) if doc else None


    
    async def insert_conversation(
        self,
        conversation: Conversation,
        pair_key: str,
    ) -> None:
        doc = conversation_to_doc(conversation=conversation, pair_key=pair_key)
        if conversation.participant_firebase_uids:
            doc["participant_firebase_uids"] = conversation.participant_firebase_uids
        try:
            await self._conversations.insert_one(doc)
        except DuplicateKeyError as exc:
            raise ConflictError("Conversation already exists") from exc

    async def list_conversations_for_user(self, user_id: str) -> List[Conversation]:
        cursor = (
            self._conversations.find({"participants": user_id})
            .sort([("last_message.timestamp", DESCENDING), ("created_at", DESCENDING)])
        )
        docs = await cursor.to_list(length=None)
        return [doc_to_conversation(doc) for doc in docs]

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        doc = await self._conversations.find_one({"_id": _uuid_to_str(conversation_id)})
        return doc_to_conversation(doc) if doc else None

    async def list_messages(self, conversation_id: UUID) -> List[Message]:
        cursor = (
            self._messages.find({"conversation_id": _uuid_to_str(conversation_id)})
            .sort([("timestamp", ASCENDING)])
        )
        docs = await cursor.to_list(length=None)
        return [_doc_to_message(doc) for doc in docs]

    async def insert_message(self, message: Message) -> None:
        doc = {
            "_id": _uuid_to_str(message.id),
            "conversation_id": _uuid_to_str(message.conversation_id),
            "sender_uid": message.sender_uid,
            "content": message.content,
            "timestamp": message.timestamp,
            "read_by": message.read_by,
        }
        if message.image_ids:
            doc["image_ids"] = [_uuid_to_str(i) for i in message.image_ids]
            
        await self._messages.insert_one(doc)

    async def set_conversation_last_message(
        self,
        conversation_id: UUID,
        last_message: LastMessage,
    ) -> None:
        await self._conversations.update_one(
            {"_id": _uuid_to_str(conversation_id)},
            {
                "$set": {
                    "last_message": {
                        "content": last_message.content,
                        "sender_uid": last_message.sender_uid,
                        "timestamp": last_message.timestamp,
                    }
                }
            },
        )

    async def mark_messages_read(self, conversation_id: UUID, user_id: str) -> int:
        """
        Adds user_id to read_by on every message in the conversation where it isn't already present.
        Returns the number of messages modified.
        """
        result = await self._messages.update_many(
            {
                "conversation_id": _uuid_to_str(conversation_id),
                "read_by": {"$ne": user_id},
            },
            {"$addToSet": {"read_by": user_id}},
        )
        return int(result.modified_count)

    async def get_by_listing_id_and_participant(
        self,
        listing_id : UUID,
        participants: List[str]
    ) -> Optional[Conversation]:
        doc = await self._conversations.find_one(
            {
                "listing_id": _uuid_to_str(listing_id),
                "participants": {"$all": participants},
            }
        )
        return doc_to_conversation(doc) if doc else None

    async def get_conversations_by_listing_id(
        self, 
        listing_id: UUID
        ) -> Optional[List[Conversation]]:
        docs = await self._conversations.find(
            {
                "listing_id": _uuid_to_str(listing_id),
            }
        ).to_list(length=None)
        return [doc_to_conversation(doc) for doc in docs]
    
    async def delete_message_by_id(self, message_id: UUID) -> None:
        await self._messages.delete_one({"_id": _uuid_to_str(message_id)})
        
    async def delete_conversation(self, conversation_id: UUID) -> None:
        await self._conversations.delete_one({"_id": _uuid_to_str(conversation_id)})
        await self._messages.delete_many({"conversation_id": _uuid_to_str(conversation_id)})