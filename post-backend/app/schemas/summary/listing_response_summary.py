"""
Fichier de la classe ListingResponseSummary
"""

import uuid
from pydantic import BaseModel, Field

from app.schemas.damage_state import DamageState
from app.schemas.image import Image
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.sold_state import SoldState

import app.schemas.listing as listing

class ListingResponseSummary(BaseModel):
    """Objet de réponse minimalisé"""
    id: uuid.UUID = Field()
    vendor_id: str = Field(min_length=listing.VENDOR_ID_LENGTH, 
                           max_length=listing.VENDOR_ID_LENGTH)
    book_id: str = Field(min_length=listing.BOOK_ID_LENGTH,
                         max_length=listing.BOOK_ID_LENGTH)
    title: str = Field(min_length=listing.TITLE_MIN_LENGTH,
                       max_length=listing.TITLE_MAX_LENGTH)
    damage_state: DamageState
    sold_state: SoldState
    price: float = Field(gt=listing.PRICE_MIN_VALUE, lt=listing.PRICE_MAX_VALUE)
    shipping_offer: ShippingOffer
    location: str = Field(min_length=listing.LOCATION_MIN_LENGTH, 
                          max_length=listing.LOCATION_MAX_LENGTH)
    is_annoted: bool = Field(default=False)
    seller_rep: int = Field(ge=listing.SELLER_REP_MIN_LENGTH, 
                            le=listing.SELLER_REP_MAX_LENGTH)
    first_image: Image | None = Field(None)
    book_categories: list[str] = Field(default_factory=list, description="Book type categories from Google Books (for recommendations)")
    view_count: int = Field(default=0, ge=0, description="Number of unique user views")
