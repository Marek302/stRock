"""
Objet de domaine pour les images
"""
import uuid
from pydantic import Field, BaseModel

MIN_IMAGE_INDEX = 0
MAX_IMAGE_INDEX = 10

class Image(BaseModel):
    """
    Objet de domaine
    """
    id: uuid.UUID | None = Field()
    image_index: int = Field(ge=MIN_IMAGE_INDEX, le=MAX_IMAGE_INDEX)
    listing_id: uuid.UUID | None = Field()