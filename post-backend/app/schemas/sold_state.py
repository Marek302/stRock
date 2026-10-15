"""

    Objet de domaine: vérification des entrées avant la convertion en entité
    
"""

from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.core.enums import SoldStateId

SOLD_STATE_MIN_LENGTH = 3
SOLD_STATE_MAX_LENGTH = 64

class SoldState(BaseModel):
    """Objet de domaine"""
    id: SoldStateId = Field()
    name: str = Field(min_length=SOLD_STATE_MIN_LENGTH,
                      max_length=SOLD_STATE_MAX_LENGTH)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v):
        """Valide les champs personnalisés"""
        if isinstance(v, UUID):
            return str(v)
        return v