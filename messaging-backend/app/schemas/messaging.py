
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.messaging import (
    MAX_IMAGES_PER_MESSAGE,
    MAX_MESSAGE_CONTENT_LENGTH,
    PARTICIPANTS_COUNT,
    SENDER_UID_LENGTH,
)


class CreateConversationRequest(BaseModel):
    listing_id: UUID
    
class ConversationDTO(BaseModel):
    id: UUID
    participants: List[str] = Field(min_length=PARTICIPANTS_COUNT, max_length=PARTICIPANTS_COUNT)
    listing_id: UUID
    created_at: datetime
    last_message: Optional["LastMessageDTO"] = None
    other_participant_firebase_uid: Optional[str] = Field(None, min_length=SENDER_UID_LENGTH, max_length=SENDER_UID_LENGTH)

    @field_validator("participants")
    @classmethod
    def check_participants_length(cls, v: List[str]) -> List[str]:
        for p in v:
            if len(p) != SENDER_UID_LENGTH:
                raise ValueError(f"Participant UID must be {SENDER_UID_LENGTH} characters long")
        return v


class LastMessageDTO(BaseModel):
    content: str
    sender_uid: str = Field(min_length=SENDER_UID_LENGTH, max_length=SENDER_UID_LENGTH)
    timestamp: datetime


ConversationDTO.model_rebuild()


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=0, max_length=MAX_MESSAGE_CONTENT_LENGTH)
    image_ids: Optional[List[UUID]] = Field(default=None, max_length=MAX_IMAGES_PER_MESSAGE)

    @model_validator(mode="after")
    def check_content_or_images(self) -> "SendMessageRequest":
        if not self.content.strip() and not self.image_ids:
            raise ValueError("Message must have either content or images")
        return self


class MessageDTO(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_uid: str = Field(min_length=SENDER_UID_LENGTH, max_length=SENDER_UID_LENGTH)
    content: str
    image_ids: Optional[List[UUID]] = None
    timestamp: datetime
    read_by: List[str] = Field(min_length=1, max_length=PARTICIPANTS_COUNT)

    @model_validator(mode="after")
    def check_content_or_images(self) -> "MessageDTO":
        if not self.content.strip() and not self.image_ids:
            raise ValueError("Message must have either content or images")
        return self

    @field_validator("read_by")
    @classmethod
    def check_read_by_length(cls, v: List[str]) -> List[str]:
        for p in v:
            if len(p) != SENDER_UID_LENGTH:
                raise ValueError(f"Participant UID must be {SENDER_UID_LENGTH} characters long")
        return v

class MarkReadResponse(BaseModel):
    updated: int


class DeleteConversationsRequest(BaseModel):
    conversation_ids: List[UUID]
