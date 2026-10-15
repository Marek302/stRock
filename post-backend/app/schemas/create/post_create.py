"""
Fichier de la classe PostCreate
"""
import uuid
from pydantic import BaseModel, Field, field_validator

from app.schemas.create.image_create import ImageCreate
import app.schemas.post as post

class PostCreate(BaseModel):
    """Objet de création d'un Post"""
    book_id: str = Field(min_length=post.BOOK_ID_LENGTH,
                         max_length=post.BOOK_ID_LENGTH)
    title: str = Field(min_length=post.TITLE_MIN_LENGTH,
                       max_length=post.TITLE_MAX_LENGTH)
    damage_state_id: uuid.UUID = Field()
    sold_state_id: uuid.UUID = Field(default=uuid.UUID("d8a683fb-f74a-41ee-af5a-59bc574a7b15"))
    description: str = Field(min_length=post.DESCRIPTION_MIN_LENGTH,
                             max_length=post.DESCRIPTION_MAX_LENGTH)
    price: float = Field(gt=post.PRICE_MIN_VALUE, lt=post.PRICE_MAX_VALUE)
    shipping_offer_id: uuid.UUID = Field()
    location: str = Field(min_length=post.LOCATION_MIN_LENGTH,
                          max_length=post.LOCATION_MAX_LENGTH)
    is_annoted: bool = Field(default=False)
    seller_rep: int = Field(ge=post.SELLER_REP_MIN_LENGTH, le=post.SELLER_REP_MAX_LENGTH)
    buyer: str | None = Field(default=None, min_length=post.USER_ID_LENGTH, max_length=post.USER_ID_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    images: list[ImageCreate] = Field(default=[])

    @field_validator("images")
    @classmethod
    def check_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("A post needs at least one image")
        return v
