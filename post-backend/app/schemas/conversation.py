"""
Objet de domaine pour les conversations
"""
import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from app.schemas.last_message import LastMessage

class Conversation(BaseModel):
    """Objet de domaine"""
    id: UUID
    participants: List[str] = Field(min_length=2, max_length=2)
    post_id: UUID
    created_at: datetime.datetime
    last_message: Optional[LastMessage] = None
    other_participant_firebase_uid: Optional[str] = Field(None, min_length=28, max_length=28)

    @field_validator("participants")
    @classmethod
    def check_participants_length(cls, v: List[str]) -> List[str]:
        for p in v:
            if len(p) != 28:
                raise ValueError("Participant UID must be 28 characters long")
        return v

Conversation.model_rebuild()
