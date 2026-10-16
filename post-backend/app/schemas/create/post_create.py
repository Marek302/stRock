"""Création d'un contenu, sans champs commerciaux."""
from pydantic import ConfigDict, Field, field_validator, model_validator
from app.schemas.post import PostDetails, PostType
from app.schemas.create.image_create import ImageCreate

class PostCreate(PostDetails):
    model_config = ConfigDict(extra="forbid")
    images: list[ImageCreate] = Field(default_factory=list, max_length=11)
    expiration_hours: int | None = Field(default=None, ge=1, le=240)

    @model_validator(mode="after")
    def require_publication_location(self):
        if self.content_type == PostType.PUBLICATION and (
            self.latitude is None or not self.location or not self.location.strip()
        ):
            raise ValueError("Une publication exige un lieu et ses coordonnées")
        return self

    @model_validator(mode="after")
    def require_publication_duration(self):
        if self.content_type == PostType.PUBLICATION and self.expiration_hours is None:
            raise ValueError("Une publication exige une durée entre 1 heure et 10 jours")
        if self.content_type != PostType.PUBLICATION and self.expiration_hours is not None:
            raise ValueError("La durée personnalisée est réservée aux publications")
        return self

    @field_validator("images")
    @classmethod
    def unique_image_indexes(cls, images):
        indexes = [image.image_index for image in images]
        if len(set(indexes)) != len(indexes):
            raise ValueError("Chaque image doit avoir un index distinct")
        return images
