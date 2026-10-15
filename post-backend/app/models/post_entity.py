"""

Classe pour l'entité Post

"""
import uuid
from pydantic import field_validator
from sqlalchemy import Column, SmallInteger, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlmodel import Field, SQLModel, Relationship

from app.models.image_entity import ImageEntity


USER_ID_LENGTH = 28
BOOK_ID_LENGTH = 12

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 128

DESCRIPTION_MIN_LENGTH = 24
DESCRIPTION_MAX_LENGTH = 1024

PRICE_MIN_VALUE = 0.0
PRICE_MAX_VALUE = 10000.00

LOCATION_MIN_LENGTH = 3
LOCATION_MAX_LENGTH = 128

SELLER_REP_MIN_LENGTH = 0
SELLER_REP_MAX_LENGTH = 10

class PostEntity(SQLModel, table=True):
    """Entité de la base de données"""
    __tablename__ = "post"
    id: uuid.UUID | None = Field(primary_key=True, default_factory=uuid.uuid4)

    user_id: str = Field(min_length=USER_ID_LENGTH,max_length=USER_ID_LENGTH, nullable=False)
    title: str = Field(min_length=TITLE_MIN_LENGTH,
                       max_length=TITLE_MAX_LENGTH,
                       nullable=False)

    description: str = Field(max_length=DESCRIPTION_MAX_LENGTH, nullable=False)


    location: str = Field(default="Unknown",min_length=LOCATION_MIN_LENGTH,
                          max_length=LOCATION_MAX_LENGTH, nullable=False)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    images: list["ImageEntity"] = Relationship(back_populates="post",
                                               sa_relationship_kwargs={"cascade": "all, delete-orphan"})
