"""Conversions entre les contrats HTTP et la base de données."""
from uuid import uuid4
from app.models.image_entity import ImageEntity
from app.models.post_entity import PostEntity
from app.schemas.post import Post
from app.schemas.summary.post_list_response import PostListResponse

class PostMapper:
    @staticmethod
    def to_entity(schema, user_id):
        post_id = uuid4()
        return PostEntity(
            id=post_id, user_id=user_id,
            **schema.model_dump(exclude={"images"}),
            images=[ImageEntity(id=(image_id := uuid4()), post_id=post_id,
                image_index=img.image_index,
                image_path=f"/{user_id}/{post_id}/{image_id}") for img in schema.images],
        )

    @staticmethod
    def to_schema(entity):
        return Post.model_validate(entity)

    to_summary = to_schema

    @staticmethod
    def to_list_response(posts, count, skip, limit):
        return PostListResponse(posts=[PostMapper.to_schema(p) for p in posts], count=count, skip=skip, limit=limit)
