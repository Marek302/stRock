"""
Modèle de base de données pour les images.
"""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.listing_entity import ListingEntity

class ImageEntity(SQLModel, table=True):
    """Représente la table 'image' dans la base de données."""
    __tablename__ = "image"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    image_path: str = Field(nullable=False)
    image_index: int = Field(nullable=False)
    listing_id: UUID = Field(foreign_key="listing.id", nullable=False)
    listing: "ListingEntity" = Relationship(back_populates="images")