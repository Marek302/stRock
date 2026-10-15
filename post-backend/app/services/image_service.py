"""
Fichier du service ImageService
"""
import uuid
from fastapi import Depends 
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.image_entity import ImageEntity
from app.services.service_exceptions import NotFoundException


class ImageService:
    """
    Service dédié aux opération qui concerne seulement l'objet image
    """

    def __init__(self, session: Session):
        """Initialisation du service"""
        self.session = session

    @staticmethod
    async def get_image_service(session: Session = Depends(get_session)) -> "ImageService":
        """Retourne une nouvelle instance du service"""
        return ImageService(session)

    async def get_by_id(self, image_id: uuid.UUID) -> ImageEntity:
        """Retourne ImageEntity par son index et listing_id"""
        statement = select(ImageEntity).where(
            ImageEntity.id == image_id
        )
        result = self.session.exec(statement)
        image = result.first()
        if not image:
            raise NotFoundException(f"""image with id {image_id} 
                                    was not found.""")
        return image
    
    async def delete_entity(self, entity: ImageEntity) -> None:
        """Supprime une image par son id"""
        await self.session.delete(entity)
        await self.session.commit()
    

    
    