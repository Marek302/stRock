"""Coordonnées géographiques d'une publication."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PostLocation(BaseModel):
    """Projection minimale d'une publication pour la carte."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    latitude: float | None
    longitude: float | None
