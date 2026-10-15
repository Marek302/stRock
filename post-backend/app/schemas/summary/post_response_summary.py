"""
Fichier de la classe PostResponseSummary
"""

import uuid
from pydantic import BaseModel, Field

from app.schemas.image import Image

import app.schemas.post as post

class PostResponseSummary(BaseModel):
    """Objet de réponse minimalisé"""
    id: uuid.UUID = Field()
    user_id: str = Field(min_length=post.USER_ID_LENGTH,
                           max_length=post.USER_ID_LENGTH)
    title: str = Field(min_length=post.TITLE_MIN_LENGTH,
                       max_length=post.TITLE_MAX_LENGTH)
    description: str = Field(max_length=post.DESCRIPTION_MAX_LENGTH)
    location: str = Field(min_length=post.LOCATION_MIN_LENGTH,
                          max_length=post.LOCATION_MAX_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    first_image: Image | None = Field(None)
