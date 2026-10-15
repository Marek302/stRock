from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# TODO: EDIT TO MATCH NEW SHCHEMA

class DamageState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str

class SoldState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str

class ShippingOffer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    delivery_offer: bool

class Image(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    image_path: str | None = None
    image_index: int = 0
    listing_id: UUID | None = None

class Listing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    vendor_id: str
    book_id: str
    title: str
    description: str
    price: float
    damage_state: DamageState
    sold_state: SoldState
    shipping_offer: ShippingOffer
    location: str
    seller_rep: int
    is_annoted: bool
    buyer: Optional[str] = None
    images: List[Image] = []
