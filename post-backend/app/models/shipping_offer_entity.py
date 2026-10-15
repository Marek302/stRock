"""

Entitié du modèle pour l'offre de vente

"""
import uuid
from sqlmodel import Field, SQLModel


SHIPPING_OFFER_MIN_LENGTH = 3
SHIPPING_OFFER_MAX_LENGTH = 64

class ShippingOfferEntity(SQLModel, table=True):
    """Entité de la base de données"""
    __tablename__ = "shipping_offer"
    id: uuid.UUID = Field(primary_key=True)
    name: str = Field(min_length=SHIPPING_OFFER_MIN_LENGTH,
                      max_length=SHIPPING_OFFER_MAX_LENGTH,
                      nullable=False)
    delivery_offer: bool = Field(default=False, nullable=False)
    
