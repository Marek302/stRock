"""
Fichier du service ImageService
"""
import uuid
from fastapi import Request
from app.models.image import Image
from app.models.messaging import Conversation
from app.services.service_exceptions import NotFoundException
from typing import Protocol, Optional

class ImageRepository(Protocol):
    async def get_by_id(self, image_id: uuid.UUID) -> Optional[Image]:
        ...
    async def insert(self, image: Image) -> None:
        ...
    async def delete(self, image_id: uuid.UUID) -> None:
        ...

class ImageService:
    """
    Service dédié aux opérations qui concernent seulement l'objet image
    """

    def __init__(self, repo: ImageRepository):
        """Initialisation du service"""
        self.repo = repo

    @staticmethod
    async def get_image_service(request: Request) -> "ImageService":
        """Retourne une nouvelle instance du service"""
        return request.app.state.image_service


    async def get_by_id(self, image_id: uuid.UUID) -> Image:
        """Retourne Image par son id"""
        image = await self.repo.get_by_id(image_id)
        if not image:
            raise NotFoundException(f"image with id {image_id} was not found.")
        return image

    async def create_image(self, conversation: Conversation) -> Image:
        """Crée une nouvelle entité Image"""
        image_id = uuid.uuid4()
        image_path = f"/{conversation.id}/{image_id}"
        image = Image(
            id=image_id,
            image_path=image_path,
            conversation=conversation
        )
        await self.repo.insert(image)
        return image

    async def delete(self, image_id: uuid.UUID) -> None:
        """Supprime une entité Image"""
        await self.repo.delete(image_id)
