"""
Fichier de la classe PostMapper
"""
from typing import List
from uuid import uuid4, UUID

from app.models.image_entity import ImageEntity
from app.models.post_entity import PostEntity
from app.schemas.create.post_create import PostCreate
from app.schemas.post import Post
from app.schemas.summary.post_list_response import PostListResponse
from app.schemas.summary.post_response_summary import PostResponseSummary
from app.schemas.image import Image

class PostMapper:
    """
    Classe utilitaire pour la conversion entre les schémas et les entités Post.
    """
    @staticmethod
    def to_entity(schema: PostCreate, user_id: str) -> PostEntity:
        """Convertit un PostCreate en PostEntity"""
        new_post_id = uuid4()

        image_entities = []
        for img_schema in schema.images:
            img_id = uuid4()
            image_entities.append(
                ImageEntity(
                    id=img_id,
                    image_path=f"/{user_id}/{new_post_id}/{img_id}",
                    image_index=img_schema.image_index,
                    post_id=new_post_id
                )
            )

        return PostEntity(
            id=new_post_id,
            user_id=user_id,
            title=schema.title,
            description=schema.description,
            location=schema.location,
            latitude=schema.latitude,
            longitude=schema.longitude,
            is_annoted=schema.is_annoted,
            images=image_entities
        )

    @staticmethod
    def to_schema(entity: PostEntity) -> Post:
        """Convertit une PostEntity en Post"""
        return Post(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            description=entity.description,
            price=entity.price,
            location=entity.location,
            latitude=entity.latitude,
            longitude=entity.longitude,
            images=[
                Image(
                    id=image.id,
                    image_path=image.image_path,
                    image_index=image.image_index,
                    post_id=image.post_id
                ) for image in entity.images
            ]
        )

    @staticmethod
    def to_summary(entity: PostEntity) -> PostResponseSummary:
        """Convertit une PostEntity en PostResponseSummary"""
        return PostResponseSummary(
            id=entity.id,
            user_id=entity.user_id,
            title=entity.title,
            description=entity.description,
            location=entity.location,
            latitude=entity.latitude,
            longitude=entity.longitude,
            first_image=Image(
                id=entity.images[0].id,
                image_path=entity.images[0].image_path,
                image_index=entity.images[0].image_index,
                post_id=entity.images[0].post_id
            ) if entity.images else None
        )

    @staticmethod
    def to_list_response(posts: List[PostEntity], count: int, skip: int, limit: int) -> PostListResponse:
        """Convertit une liste de PostEntity en PostListResponse"""
        return PostListResponse(
            posts=[PostMapper.to_summary(post) for post in posts],
            count=count,
            skip=skip,
            limit=limit
        )
