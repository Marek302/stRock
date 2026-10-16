"""Persistance des publications, événements et alertes."""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, Index
from sqlmodel import Field, Relationship, SQLModel
from app.models.image_entity import ImageEntity

class PostEntity(SQLModel, table=True):
    __tablename__ = "post"
    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 3 AND 128", name="post_title_length"),
        CheckConstraint("length(description) BETWEEN 1 AND 5000", name="post_description_length"),
        CheckConstraint("content_type IN ('publication', 'event', 'urban_alert', 'safety_alert')", name="post_type_check"),
        CheckConstraint("(latitude IS NULL) = (longitude IS NULL)", name="post_coordinate_pair"),
        CheckConstraint("latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180", name="post_coordinate_range"),
        CheckConstraint("content_type = 'publication' OR latitude IS NOT NULL", name="post_required_coordinates"),
        CheckConstraint("(content_type = 'event' AND starts_at IS NOT NULL AND ends_at IS NOT NULL AND ends_at > starts_at) OR (content_type <> 'event' AND starts_at IS NULL AND ends_at IS NULL)", name="post_event_dates"),
        CheckConstraint("(content_type IN ('urban_alert', 'safety_alert') AND expires_at IS NOT NULL AND expires_at > created_at) OR (content_type = 'publication' AND closed_at IS NULL AND (expires_at IS NULL OR expires_at > created_at)) OR (content_type = 'event' AND expires_at IS NULL AND closed_at IS NULL)", name="post_alert_lifecycle"),
        Index("ix_post_created_at", "created_at"),
        Index("ix_post_content_type_expires_at", "content_type", "expires_at"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(max_length=128, nullable=False, index=True)
    title: str = Field(max_length=128, nullable=False)
    description: str = Field(max_length=5000, nullable=False)
    content_type: str = Field(default="publication", max_length=32, nullable=False)
    location: str | None = Field(default=None, max_length=256)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    starts_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ends_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    closed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    images: list["ImageEntity"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
