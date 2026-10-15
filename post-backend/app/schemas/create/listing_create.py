"""
Fichier de la classe ListingCreate
"""
import uuid
from pydantic import BaseModel, Field, field_validator

from app.schemas.create.image_create import ImageCreate
import app.schemas.listing as listing
import app.core.enums as enums

class ListingCreate(BaseModel):
    """Objet de création d'un Listing"""
    book_id: str = Field(min_length=listing.BOOK_ID_LENGTH,
                         max_length=listing.BOOK_ID_LENGTH)
    title: str = Field(min_length=listing.TITLE_MIN_LENGTH,
                       max_length=listing.TITLE_MAX_LENGTH)
    damage_state_id: uuid.UUID = Field()
    sold_state_id: uuid.UUID = Field(default=enums.SoldStateId.DRAFT.value)
    description: str = Field(min_length=listing.DESCRIPTION_MIN_LENGTH,
                             max_length=listing.DESCRIPTION_MAX_LENGTH)
    price: float = Field(gt=listing.PRICE_MIN_VALUE, lt=listing.PRICE_MAX_VALUE)
    shipping_offer_id: uuid.UUID = Field()
    location: str = Field(min_length=listing.LOCATION_MIN_LENGTH, 
                          max_length=listing.LOCATION_MAX_LENGTH)
    is_annoted: bool = Field(default=False)
    seller_rep: int = Field(ge=listing.SELLER_REP_MIN_LENGTH, le=listing.SELLER_REP_MAX_LENGTH)
    buyer: str | None = Field(default=None, min_length=listing.VENDOR_ID_LENGTH, max_length=listing.VENDOR_ID_LENGTH)
    images: list[ImageCreate] = Field(default=[])

    @field_validator("images")
    @classmethod
    def check_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("A listing needs at least one image")
        return v
