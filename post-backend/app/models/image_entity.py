"""
Modèle de base de données pour les images.
"""
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint, UniqueConstraint

if TYPE_CHECKING:
    from app.models.post_entity import PostEntity

class ImageEntity(SQLModel, table=True):
    """Représente la table 'image' dans la base de données."""
    __tablename__ = "image"
    __table_args__ = (
        CheckConstraint("image_index BETWEEN 0 AND 10", name="image_index_range"),
        UniqueConstraint("post_id", "image_index"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    image_path: str = Field(nullable=False, unique=True)
    image_index: int = Field(nullable=False)
    post_id: UUID = Field(foreign_key="post.id", nullable=False)
    post: "PostEntity" = Relationship(back_populates="images")
