"""
Objet de domaine pour les images
"""
from pydantic import Field, BaseModel

import app.schemas.image as image

class ImageCreate(BaseModel):
    """
    Objet de domaine
    """
    image_index: int = Field(le=image.MAX_IMAGE_INDEX, ge=image.MIN_IMAGE_INDEX)