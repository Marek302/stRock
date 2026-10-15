from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

SENDER_UID_LENGTH = 28
PARTICIPANTS_COUNT = 2
MAX_MESSAGE_CONTENT_LENGTH = 2000
MAX_LAST_MESSAGE_CONTENT_LENGTH = 32
MAX_IMAGES_PER_MESSAGE = 3

class LastMessage(BaseModel):
    content: str = Field(max_length=MAX_LAST_MESSAGE_CONTENT_LENGTH)
    sender_uid: str = Field(min_length=SENDER_UID_LENGTH, max_length=SENDER_UID_LENGTH)
    timestamp: datetime


class Conversation(BaseModel):
    id: UUID
    listing_id: UUID
    participants: List[str] = Field(min_length=PARTICIPANTS_COUNT, max_length=PARTICIPANTS_COUNT)
    created_at: datetime
    last_message: Optional[LastMessage] = None
    participant_firebase_uids: Optional[Dict[str, str]] = None

    @field_validator("participants")
    @classmethod
    def check_participants_length(cls, v: List[str]) -> List[str]:
        for p in v:
            if len(p) != SENDER_UID_LENGTH:
                raise ValueError(f"Participant UID must be {SENDER_UID_LENGTH} characters long")
        return v

    @field_validator("participant_firebase_uids")
    @classmethod
    def check_firebase_uids_length(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        if v:
            for uid in v.values():
                if len(uid) != SENDER_UID_LENGTH:
                    raise ValueError("Firebase UID must be 28 characters long")
        return v

class Message(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_uid: str = Field(min_length=SENDER_UID_LENGTH, max_length=SENDER_UID_LENGTH)

    content: str = Field(min_length=0, max_length=MAX_MESSAGE_CONTENT_LENGTH)
    image_ids: Optional[List[UUID]] = Field(default=None, max_length=MAX_IMAGES_PER_MESSAGE)
    timestamp: datetime
    read_by: List[str] = Field(min_length=1, max_length=PARTICIPANTS_COUNT)

    @model_validator(mode="after")
    def check_content_or_images(self) -> "Message":
        if not self.content.strip() and not self.image_ids:
            raise ValueError("Message must have either content or images")
        return self

    @field_validator("read_by")
    @classmethod
    def check_participants_length(cls, v: List[str]) -> List[str]:
        for p in v:
            if len(p) != SENDER_UID_LENGTH:
                raise ValueError(f"Participant UID must be {SENDER_UID_LENGTH} characters long")
        return v
