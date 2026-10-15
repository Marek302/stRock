"""Création d'un contenu, sans champs commerciaux."""
from pydantic import ConfigDict, Field, field_validator
from app.schemas.post import PostDetails
from app.schemas.create.image_create import ImageCreate

class PostCreate(PostDetails):
    model_config = ConfigDict(extra="forbid")
    images: list[ImageCreate] = Field(default_factory=list, max_length=11)

    @field_validator("images")
    @classmethod
    def unique_image_indexes(cls, images):
        indexes = [image.image_index for image in images]
        if len(set(indexes)) != len(indexes):
            raise ValueError("Chaque image doit avoir un index distinct")
        return images
