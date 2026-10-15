"""

    Objet de domaine: vérification des entrées avant la convertion en entité
    
"""

import uuid
from pydantic import BaseModel, Field, field_validator

from app.schemas.damage_state import DamageState
from app.schemas.image import Image
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.sold_state import SoldState

VENDOR_ID_LENGTH = 28
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

class Listing(BaseModel):
    """Objet de domaine"""
    id: uuid.UUID | None = Field()
    vendor_id: str = Field(min_length=VENDOR_ID_LENGTH, 
                           max_length=VENDOR_ID_LENGTH)
    book_id: str = Field(min_length=BOOK_ID_LENGTH,
                         max_length=BOOK_ID_LENGTH)
    title: str = Field(min_length=TITLE_MIN_LENGTH,
                       max_length=TITLE_MAX_LENGTH)
    damage_state: DamageState
    sold_state: SoldState
    description: str = Field(min_length=DESCRIPTION_MIN_LENGTH,
                             max_length=DESCRIPTION_MAX_LENGTH)
    price: float = Field(gt=PRICE_MIN_VALUE, lt=PRICE_MAX_VALUE)
    shipping_offer: ShippingOffer
    location: str = Field(min_length=LOCATION_MIN_LENGTH, max_length=LOCATION_MAX_LENGTH)
    is_annoted: bool = Field(default=False)
    seller_rep: int = Field(ge=SELLER_REP_MIN_LENGTH, le=SELLER_REP_MAX_LENGTH)
    buyer: str | None = Field(min_length=VENDOR_ID_LENGTH, max_length=VENDOR_ID_LENGTH)
    images: list["Image"] = Field(default=[])
    book_categories: list[str] = Field(default_factory=list, description="Book type categories from Google Books")
    view_count: int = Field(default=0, ge=0, description="Number of unique user views")

    @field_validator("images")
    @classmethod
    def check_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("A listing needs at least one image")
        return v

