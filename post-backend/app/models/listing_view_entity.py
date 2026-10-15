"""
Entity for tracking which users have viewed which listings (once per user).
"""
import uuid

from sqlmodel import Field, SQLModel


class ListingViewEntity(SQLModel, table=True):
    """Tracks unique views per user per listing."""
    __tablename__ = "listing_view"

    listing_id: uuid.UUID = Field(primary_key=True, foreign_key="listing.id")
    user_id: str = Field(primary_key=True, max_length=28)
