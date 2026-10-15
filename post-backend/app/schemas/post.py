"""Contrat des contenus communautaires Saint-Roch."""
from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from app.schemas.image import Image

USER_ID_LENGTH = 128
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 128
DESCRIPTION_MIN_LENGTH = 1
DESCRIPTION_MAX_LENGTH = 5000
LOCATION_MIN_LENGTH = 1
LOCATION_MAX_LENGTH = 256

class PostType(str, Enum):
    PUBLICATION = "publication"
    EVENT = "event"
    URBAN_ALERT = "urban_alert"
    SAFETY_ALERT = "safety_alert"

class PostDetails(BaseModel):
    title: str = Field(min_length=TITLE_MIN_LENGTH, max_length=TITLE_MAX_LENGTH)
    description: str = Field(min_length=DESCRIPTION_MIN_LENGTH, max_length=DESCRIPTION_MAX_LENGTH)
    content_type: PostType = PostType.PUBLICATION
    location: str | None = Field(default=None, min_length=1, max_length=LOCATION_MAX_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_content(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude et longitude doivent être fournies ensemble")
        if self.content_type != PostType.PUBLICATION and self.latitude is None:
            raise ValueError("Ce type de contenu doit être géolocalisé")
        if self.content_type == PostType.EVENT:
            if self.starts_at is None or self.ends_at is None or self.ends_at <= self.starts_at:
                raise ValueError("Un événement exige une fin postérieure au début")
        elif self.starts_at is not None or self.ends_at is not None:
            raise ValueError("Les dates de début et fin sont réservées aux événements")
        return self

class Post(PostDetails):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: str = Field(min_length=1, max_length=USER_ID_LENGTH)
    created_at: datetime
    expires_at: datetime | None = None
    closed_at: datetime | None = None
    images: list[Image] = Field(default_factory=list)
