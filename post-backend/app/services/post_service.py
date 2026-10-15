"""

Service: s'occupe de récupérer les données de la BD

"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update, col
from fastapi import Depends
from app.core.db import get_session
from app.models.post_entity import PostEntity
from app.models.post_view_entity import PostViewEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.core.enums import SoldStateId
from app.schemas.create.post_create import PostCreate
from app.mappers.post_mapper import PostMapper
from app.services.service_exceptions import NotFoundException
from app.services.books_api_client import fetch_volume_categories


class PostService:
    """Classe du service"""
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    async def get_post_service(session: Session = Depends(get_session)) -> "PostService":
        """Récupération du service"""
        return PostService(session)

    def create(self, post: PostCreate, user_id: str) -> PostEntity:
        """Création des entités; fetches book_categories from Books API and stores on post."""
        post_entity = PostMapper.to_entity(post, user_id)
        categories = fetch_volume_categories(post_entity.book_id)
        post_entity.book_categories = categories if categories else []
        self.session.add(post_entity)
        self.session.commit()
        self.session.refresh(post_entity)
        return post_entity

    def get_by_id(self, post_id: str) -> PostEntity:
        """Récupération d'une entité par son ID"""
        try:
            UUID(post_id)
        except (ValueError, TypeError):
            raise NotFoundException(f"Post with id {post_id} not found")
        post = self.session.get(PostEntity, post_id)
        if not post:
            raise NotFoundException(f"Post with id {post_id} not found")
        return post

    def save(self, entity: PostEntity) -> PostEntity:
        """Update d'un post"""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_by_id(self, entity: PostEntity) -> None:
        """Delete post by id"""
        self.session.delete(entity)
        self.session.commit()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        delivery_offer: Optional[bool] = None,
        is_annoted: Optional[bool] = None,
        min_seller_rep: Optional[int] = None,
        sort_by_price: Optional[str] = None,
        exclude_post_ids: Optional[List[str]] = None,
    ) -> List[PostEntity]:
        """Récupération de multiples posts avec filtres"""
        statement = select(PostEntity)
        filters = []
        filters.append(col(PostEntity.sold_state_id) != SoldStateId.DRAFT.value)
        filters.append(col(PostEntity.buyer).is_(None))
        if exclude_post_ids:
            try:
                from uuid import UUID
                exclude_uuids = [UUID(lid) for lid in exclude_post_ids if lid]
                if exclude_uuids:
                    filters.append(col(PostEntity.id).not_in(exclude_uuids))
            except (ValueError, TypeError):
                pass
        if search:
            filters.append(col(PostEntity.title).ilike(f"%{search}%"))

        if min_price is not None:
            filters.append(col(PostEntity.price) >= min_price)

        if max_price is not None:
            filters.append(col(PostEntity.price) <= max_price)

        if location:
            filters.append(col(PostEntity.location) == location)

        if min_seller_rep is not None:
            filters.append(col(PostEntity.seller_rep) >= min_seller_rep)

        if delivery_offer is not None:
            statement = statement.join(ShippingOfferEntity)
            filters.append(col(ShippingOfferEntity.delivery_offer) == delivery_offer)

        if is_annoted is not None:
            filters.append(col(PostEntity.is_annoted) == is_annoted)

        if filters:
            statement = statement.where(*filters)

        if sort_by_price == "asc":
            statement = statement.order_by(PostEntity.price.asc())
        elif sort_by_price == "desc":
            statement = statement.order_by(PostEntity.price.desc())

        statement = statement.offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def _record_view(self, post_id: str, user_id: str) -> bool:
        """
        Record a view for a post by a user. Increments view_count only once per user.
        Returns True if this was a new view, False if user had already viewed.
        Uses a savepoint so a duplicate insert only rolls back the savepoint, not the transaction.
        """
        post = self.get_by_id(post_id)
        try:
            with self.session.begin_nested():
                self.session.add(PostViewEntity(post_id=post.id, user_id=user_id))
        except IntegrityError:
            return False
        post.view_count += 1
        self.save(post)
        return True

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[PostEntity]:
        """Récupère les posts d'un vendeur spécifique"""
        statement = (
            select(PostEntity)
            .where(PostEntity.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def update_user_reputation(self, user_id: str, new_rep: int) -> int:
        """Met à jour la réputation sur tous les posts d'un vendeur"""
        stmt = update(PostEntity).where(
            PostEntity.user_id == user_id
        ).values(seller_rep=new_rep)
        result = self.session.exec(stmt)
        self.session.commit()
        return result.rowcount
