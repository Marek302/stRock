"""CRUD, visibilité et expiration des contenus Saint-Roch."""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, HTTPException
from sqlalchemy import or_
from sqlmodel import Session, select, col
from app.core.db import get_session
from app.models.post_entity import PostEntity
from app.schemas.post import PostType
from app.schemas.summary.post_location import PostLocation
from app.mappers.post_mapper import PostMapper
from app.services.service_exceptions import NotFoundException

class PostService:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    async def get_post_service(session: Session = Depends(get_session)):
        return PostService(session)

    def create(self, post, user_id):
        entity = PostMapper.to_entity(post, user_id)
        if entity.content_type == PostType.PUBLICATION:
            entity.expires_at = entity.created_at + timedelta(hours=post.expiration_hours)
        elif entity.content_type in (PostType.URBAN_ALERT, PostType.SAFETY_ALERT):
            entity.expires_at = entity.created_at + timedelta(hours=2)
        return self.save(entity)

    def save(self, entity):
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def get_by_id(self, post_id):
        try:
            key = UUID(str(post_id))
        except (ValueError, TypeError):
            raise NotFoundException(f"Post with id {post_id} not found")
        post = self.session.exec(select(PostEntity).where(
            PostEntity.id == key,
            or_(PostEntity.content_type != PostType.PUBLICATION,
                col(PostEntity.expires_at).is_(None),
                PostEntity.expires_at > datetime.now(timezone.utc)),
        )).first()
        if post is None:
            raise NotFoundException(f"Post with id {post_id} not found")
        return post

    def delete_expired_publications(self):
        statement = select(PostEntity).where(
            PostEntity.content_type == PostType.PUBLICATION,
            col(PostEntity.expires_at).is_not(None),
            PostEntity.expires_at <= datetime.now(timezone.utc),
        )
        expired = self.session.exec(statement).all()
        for post in expired:
            self.session.delete(post)
        if expired:
            self.session.commit()
        return len(expired)

    def delete_by_id(self, entity):
        self.session.delete(entity)
        self.session.commit()

    @staticmethod
    def _active(statement):
        return statement.where(
            col(PostEntity.closed_at).is_(None),
            or_(col(PostEntity.expires_at).is_(None), PostEntity.expires_at > datetime.now(timezone.utc)),
        )

    def list_locations(self):
        statement = self._active(select(PostEntity.id, PostEntity.latitude, PostEntity.longitude, PostEntity.content_type)).where(
            col(PostEntity.latitude).is_not(None), col(PostEntity.longitude).is_not(None))
        return [PostLocation.model_validate(row) for row in self.session.exec(statement).all()]

    def list_all(self, skip=0, limit=20, search=None, location=None, exclude_post_ids=None):
        statement = self._active(select(PostEntity)).where(PostEntity.content_type != PostType.SAFETY_ALERT)
        if exclude_post_ids:
            statement = statement.where(col(PostEntity.id).not_in(exclude_post_ids))
        if search:
            statement = statement.where(or_(col(PostEntity.title).ilike(f"%{search}%"), col(PostEntity.description).ilike(f"%{search}%")))
        if location:
            statement = statement.where(PostEntity.location == location)
        return self.session.exec(statement.order_by(col(PostEntity.created_at).desc(), PostEntity.id).offset(skip).limit(limit)).all()

    def get_by_user(self, user_id, skip=0, limit=20):
        statement = self._active(select(PostEntity)).where(PostEntity.user_id == user_id, PostEntity.content_type != PostType.SAFETY_ALERT)
        return self.session.exec(statement.order_by(col(PostEntity.created_at).desc(), PostEntity.id).offset(skip).limit(limit)).all()

    def close_alert(self, entity):
        if entity.content_type not in (PostType.URBAN_ALERT, PostType.SAFETY_ALERT):
            raise HTTPException(status_code=400, detail="Seules les alertes peuvent être clôturées")
        if entity.closed_at is None:
            entity.closed_at = datetime.now(timezone.utc)
            self.save(entity)
        return entity
