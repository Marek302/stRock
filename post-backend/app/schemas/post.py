"""

    Objet de domaine: vérification des entrées avant la convertion en entité

"""

import uuid
from pydantic import BaseModel, Field, field_validator

from app.schemas.damage_state import DamageState
from app.schemas.image import Image
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.sold_state import SoldState

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

class Post(BaseModel):
    """Objet de domaine"""
    id: uuid.UUID | None = Field()
    user_id: str = Field(min_length=USER_ID_LENGTH,
                           max_length=USER_ID_LENGTH)
    title: str = Field(min_length=TITLE_MIN_LENGTH,
                       max_length=TITLE_MAX_LENGTH)
    description: str = Field(min_length=DESCRIPTION_MIN_LENGTH,
                             max_length=DESCRIPTION_MAX_LENGTH)
    location: str = Field(min_length=LOCATION_MIN_LENGTH, max_length=LOCATION_MAX_LENGTH)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    images: list["Image"] = Field(default=[])

    @field_validator("images")
    @classmethod
    def check_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("A post needs at least one image")
        return v

