from uuid import UUID
from pydantic import BaseModel

class ImageDTO(BaseModel):
    id: UUID
    image_path: str
