"""
Modèle de base de données pour les images.
"""
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.models.messaging import Conversation

class Image(BaseModel):
    """Représente une image dans MongoDB."""
    id: UUID = Field(default_factory=uuid4, alias="_id")
    image_path: str
    conversation: Conversation
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }