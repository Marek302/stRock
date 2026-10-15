"""

Entitié du modèle pour l'offre de vente

"""
import uuid
from sqlmodel import Field, SQLModel

SOLD_STATE_MIN_LENGTH = 3
SOLD_STATE_MAX_LENGTH = 64

class SoldStateEntity(SQLModel, table=True):
    """Entité de la base de données"""
    __tablename__ = "sold_state"
    id: uuid.UUID = Field(primary_key=True)
    name: str = Field(min_length=SOLD_STATE_MIN_LENGTH,
                      max_length=SOLD_STATE_MAX_LENGTH,
                      nullable=False
                      )
    