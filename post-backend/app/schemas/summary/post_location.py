"""Coordonnées géographiques d'une publication."""
from uuid import UUID
from app.schemas.post import PostType

from pydantic import BaseModel, ConfigDict


class PostLocation(BaseModel):
    """Projection minimale d'une publication pour la carte."""

    model_config = ConfigDict(from_attributes=True)

    content_type: PostType
    id: UUID
    latitude: float | None
    longitude: float | None
