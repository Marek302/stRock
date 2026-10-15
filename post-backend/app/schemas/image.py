"""
Objet de domaine pour les images
"""
import uuid
from pydantic import Field, BaseModel, ConfigDict

MIN_IMAGE_INDEX = 0
MAX_IMAGE_INDEX = 10

class Image(BaseModel):
    """
    Objet de domaine
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = Field()
    image_index: int = Field(ge=MIN_IMAGE_INDEX, le=MAX_IMAGE_INDEX)
    post_id: uuid.UUID | None = Field()
