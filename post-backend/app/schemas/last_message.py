"""
Objet de domaine pour le dernier message d'une conversation
"""
import datetime
from pydantic import BaseModel, Field


class LastMessage(BaseModel):
    """Objet de domaine"""
    content: str
    sender_uid: str = Field(min_length=28, max_length=28)
    timestamp: datetime.datetime