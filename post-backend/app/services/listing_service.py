"""

Service: s'occupe de récupérer les données de la BD

"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, update, col
from fastapi import Depends
from app.core.db import get_session
from app.models.listing_entity import ListingEntity
from app.models.listing_view_entity import ListingViewEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.core.enums import SoldStateId
from app.schemas.create.listing_create import ListingCreate
from app.mappers.listing_mapper import ListingMapper
from app.services.service_exceptions import NotFoundException
from app.services.books_api_client import fetch_volume_categories


class ListingService:
    """Classe du service"""
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    async def get_listing_service(session: Session = Depends(get_session)) -> "ListingService":
        """Récupération du service"""
        return ListingService(session)

    def create(self, listing: ListingCreate, vendor_id: str) -> ListingEntity:
        """Création des entités; fetches book_categories from Books API and stores on listing."""
        listing_entity = ListingMapper.to_entity(listing, vendor_id)
        categories = fetch_volume_categories(listing_entity.book_id)
        listing_entity.book_categories = categories if categories else []
        self.session.add(listing_entity)
        self.session.commit()
        self.session.refresh(listing_entity)
        return listing_entity

    def get_by_id(self, listing_id: str) -> ListingEntity:
        """Récupération d'une entité par son ID"""
        try:
            UUID(listing_id)
        except (ValueError, TypeError):
            raise NotFoundException(f"Listing with id {listing_id} not found")
        listing = self.session.get(ListingEntity, listing_id)
        if not listing:
            raise NotFoundException(f"Listing with id {listing_id} not found")
        return listing

    def save(self, entity: ListingEntity) -> ListingEntity:
        """Update d'un listing"""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete_by_id(self, entity: ListingEntity) -> None:
        """Delete listing by id"""
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
        exclude_listing_ids: Optional[List[str]] = None,
    ) -> List[ListingEntity]:
        """Récupération de multiples listings avec filtres"""
        statement = select(ListingEntity)
        filters = []
        filters.append(col(ListingEntity.sold_state_id) != SoldStateId.DRAFT.value)
        filters.append(col(ListingEntity.buyer).is_(None))
        if exclude_listing_ids:
            try:
                from uuid import UUID
                exclude_uuids = [UUID(lid) for lid in exclude_listing_ids if lid]
                if exclude_uuids:
                    filters.append(col(ListingEntity.id).not_in(exclude_uuids))
            except (ValueError, TypeError):
                pass
        if search:
            filters.append(col(ListingEntity.title).ilike(f"%{search}%"))

        if min_price is not None:
            filters.append(col(ListingEntity.price) >= min_price)

        if max_price is not None:
            filters.append(col(ListingEntity.price) <= max_price)

        if location:
            filters.append(col(ListingEntity.location) == location)

        if min_seller_rep is not None:
            filters.append(col(ListingEntity.seller_rep) >= min_seller_rep)

        if delivery_offer is not None:
            statement = statement.join(ShippingOfferEntity)
            filters.append(col(ShippingOfferEntity.delivery_offer) == delivery_offer)

        if is_annoted is not None:
            filters.append(col(ListingEntity.is_annoted) == is_annoted)

        if filters:
            statement = statement.where(*filters)

        if sort_by_price == "asc":
            statement = statement.order_by(ListingEntity.price.asc())
        elif sort_by_price == "desc":
            statement = statement.order_by(ListingEntity.price.desc())

        statement = statement.offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def _record_view(self, listing_id: str, user_id: str) -> bool:
        """
        Record a view for a listing by a user. Increments view_count only once per user.
        Returns True if this was a new view, False if user had already viewed.
        Uses a savepoint so a duplicate insert only rolls back the savepoint, not the transaction.
        """
        listing = self.get_by_id(listing_id)
        try:
            with self.session.begin_nested():
                self.session.add(ListingViewEntity(listing_id=listing.id, user_id=user_id))
        except IntegrityError:
            return False
        listing.view_count += 1
        self.save(listing)
        return True

    def get_by_vendor(self, vendor_id: str, skip: int = 0, limit: int = 20) -> List[ListingEntity]:
        """Récupère les listings d'un vendeur spécifique"""
        statement = (
            select(ListingEntity)
            .where(ListingEntity.vendor_id == vendor_id)
            .offset(skip)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def update_vendor_reputation(self, vendor_id: str, new_rep: int) -> int:
        """Met à jour la réputation sur tous les listings d'un vendeur"""
        stmt = update(ListingEntity).where(
            ListingEntity.vendor_id == vendor_id
        ).values(seller_rep=new_rep)
        result = self.session.exec(stmt)
        self.session.commit()
        return result.rowcount
