"""

Entitié du modèle pour l'état d'un article

"""
import uuid
from sqlmodel import Field, SQLModel


DAMAGE_STATE_MIN_LENGTH = 3
DAMAGE_STATE_MAX_LENGTH = 64

class DamageStateEntity(SQLModel, table=True):
    """Entité de la base de données"""
    __tablename__ = "damage_state"
    id: uuid.UUID = Field(primary_key=True)
    name: str = Field(min_length=DAMAGE_STATE_MIN_LENGTH,
                      max_length=DAMAGE_STATE_MAX_LENGTH,
                      nullable=False)
    