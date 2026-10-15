"""

    Objet de domaine: vérification des entrées avant la convertion en entité
    
"""

from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.core.enums import ShippingOfferId

SHIPPING_OFFER_MIN_LENGTH = 3
SHIPPING_OFFER_MAX_LENGTH = 64

class ShippingOffer(BaseModel):
    """Objet de domaine"""
    id: ShippingOfferId = Field()
    name: str = Field(min_length=SHIPPING_OFFER_MIN_LENGTH,
                      max_length=SHIPPING_OFFER_MAX_LENGTH)
    delivery_offer: bool = Field(default=False)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        """Valide les champs personnalisés"""
        if isinstance(v, UUID):
            return str(v)
        return v
