from typing import Any, Dict, Optional
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.image import Image
from app.services.messaging_service import canonical_pair_key
from app.services.messaging_repo import doc_to_conversation, conversation_to_doc

def _uuid_to_str(value: UUID) -> str:
    return str(value)

def _str_to_uuid(value: str) -> UUID:
    return UUID(value)

def _doc_to_image(doc: Dict[str, Any]) -> Image:
    return Image(
        id=_str_to_uuid(doc["_id"]),
        image_path=doc["image_path"],
        conversation=doc_to_conversation(doc["conversation"])
    )

def _image_to_doc(image: Image):
    user_id1, user_id2, pair_key = canonical_pair_key(participants=image.conversation.participants, 
                                                      listing_id=image.conversation.listing_id)
    return {
            "_id": _uuid_to_str(image.id),
            "image_path": image.image_path,
            "conversation": conversation_to_doc(conversation=image.conversation, 
                                                pair_key=pair_key),
        }

class MongoImageRepository:
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        collection_name: str = "images",
    ):
        self._db = db
        self._collection = db[collection_name]

    async def get_by_id(self, image_id: UUID) -> Optional[Image]:
        doc = await self._collection.find_one({"_id": _uuid_to_str(image_id)})
        return _doc_to_image(doc) if doc else None

    async def insert(self, image: Image) -> None:
        doc = _image_to_doc(image=image)
        await self._collection.insert_one(doc)

    async def delete(self, image_id: UUID) -> None:
        await self._collection.delete_one({"_id": _uuid_to_str(image_id)})
