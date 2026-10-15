"""

Classe pour l'entité Listing

"""
import uuid
from pydantic import field_validator
from sqlalchemy import Column, SmallInteger, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlmodel import Field, SQLModel, Relationship

from app.models.damage_state_entity import DamageStateEntity
from app.models.image_entity import ImageEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.models.sold_state_entity import SoldStateEntity


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

class ListingEntity(SQLModel, table=True):
    """Entité de la base de données"""
    __tablename__ = "listing"
    id: uuid.UUID | None = Field(primary_key=True, default_factory=uuid.uuid4)

    vendor_id: str = Field(min_length=VENDOR_ID_LENGTH,max_length=VENDOR_ID_LENGTH, nullable=False)
    book_id: str = Field(max_length=BOOK_ID_LENGTH, nullable=False)
    title: str = Field(min_length=TITLE_MIN_LENGTH,
                       max_length=TITLE_MAX_LENGTH,
                       nullable=False)
    damage_state_id: uuid.UUID = Field(nullable=False, foreign_key='damage_state.id')
    damage_state: DamageStateEntity = Relationship()

    sold_state_id: uuid.UUID = Field(nullable=False, foreign_key='sold_state.id')
    sold_state: SoldStateEntity = Relationship()

    description: str = Field(max_length=DESCRIPTION_MAX_LENGTH, nullable=False)
    price: float = Field(gt=PRICE_MIN_VALUE, lt=PRICE_MAX_VALUE, nullable=False)

    shipping_offer_id: uuid.UUID = Field(nullable=False, foreign_key='shipping_offer.id')
    shipping_offer: ShippingOfferEntity = Relationship()

    location: str = Field(default="Unknown",min_length=LOCATION_MIN_LENGTH, 
                          max_length=LOCATION_MAX_LENGTH, nullable=False)
    is_annoted: bool = Field(default=False, nullable=False)
    seller_rep: int = Field(ge=SELLER_REP_MIN_LENGTH, 
                            le=SELLER_REP_MAX_LENGTH, 
                            default=0,
                            sa_column=SmallInteger)
    buyer: str | None = Field(min_length=VENDOR_ID_LENGTH, max_length=VENDOR_ID_LENGTH, nullable=True)
    book_categories: list[str] | None = Field(default=None, sa_column=Column(PG_ARRAY(Text), nullable=True))
    view_count: int = Field(default=0, ge=0, nullable=False)
    images: list["ImageEntity"] = Relationship(back_populates="listing",
                                               sa_relationship_kwargs={"cascade": "all, delete-orphan"})
