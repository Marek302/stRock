"""
Fichier de la classe ListingMapper
"""
from typing import List
from uuid import uuid4, UUID

from app.models.image_entity import ImageEntity
from app.models.listing_entity import ListingEntity
from app.schemas.create.listing_create import ListingCreate
from app.schemas.listing import Listing
from app.schemas.summary.listing_list_response import ListingListResponse
from app.schemas.summary.listing_response_summary import ListingResponseSummary
from app.schemas.damage_state import DamageState
from app.schemas.sold_state import SoldState
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.image import Image

class ListingMapper:
    """
    Classe utilitaire pour la conversion entre les schémas et les entités Listing.
    """
    @staticmethod
    def to_entity(schema: ListingCreate, vendor_id: str) -> ListingEntity:
        """Convertit un ListingCreate en ListingEntity"""
        new_listing_id = uuid4()
        
        image_entities = []
        for img_schema in schema.images:
            img_id = uuid4()
            image_entities.append(
                ImageEntity(
                    id=img_id,
                    image_path=f"/{vendor_id}/{new_listing_id}/{img_id}", 
                    image_index=img_schema.image_index,
                    listing_id=new_listing_id
                )
            )

        return ListingEntity(
            id=new_listing_id,
            vendor_id=vendor_id,
            book_id=schema.book_id,
            title=schema.title,
            description=schema.description,
            price=schema.price,
            damage_state_id=schema.damage_state_id,
            sold_state_id=schema.sold_state_id,
            shipping_offer_id=schema.shipping_offer_id,
            location=schema.location,
            is_annoted=schema.is_annoted,
            seller_rep=schema.seller_rep,
            buyer=schema.buyer,
            images=image_entities 
        )

    @staticmethod
    def to_schema(entity: ListingEntity) -> Listing:
        """Convertit une ListingEntity en Listing"""
        return Listing(
            id=entity.id,
            vendor_id=entity.vendor_id,
            book_id=entity.book_id,
            title=entity.title,
            description=entity.description,
            price=entity.price,
            damage_state=DamageState(
                id=str(entity.damage_state_id),
                name=entity.damage_state.name
            ),
            sold_state=SoldState(
                id=str(entity.sold_state_id),
                name=entity.sold_state.name
            ),
            shipping_offer=ShippingOffer(
                id=str(entity.shipping_offer_id),
                name=entity.shipping_offer.name,
                delivery_offer=entity.shipping_offer.delivery_offer
            ),
            location=entity.location,
            seller_rep=entity.seller_rep,
            is_annoted=entity.is_annoted,
            buyer=entity.buyer,
            book_categories=entity.book_categories or [],
            view_count=entity.view_count,
            images=[
                Image(
                    id=image.id,
                    image_path=image.image_path,
                    image_index=image.image_index,
                    listing_id=image.listing_id
                ) for image in entity.images
            ]
        )

    @staticmethod
    def to_summary(entity: ListingEntity) -> ListingResponseSummary:
        """Convertit une ListingEntity en ListingResponseSummary"""
        return ListingResponseSummary(
            id=entity.id,
            vendor_id=entity.vendor_id,
            book_id=entity.book_id,
            title=entity.title,
            damage_state=DamageState(
                id=str(entity.damage_state_id),
                name=entity.damage_state.name
            ),
            sold_state=SoldState(
                id=str(entity.sold_state_id),
                name=entity.sold_state.name
            ),
            price=entity.price,
            shipping_offer=ShippingOffer(
                id=str(entity.shipping_offer_id),
                name=entity.shipping_offer.name,
                delivery_offer=entity.shipping_offer.delivery_offer
            ),
            location=entity.location,
            is_annoted=entity.is_annoted,
            seller_rep=entity.seller_rep,
            buyer=entity.buyer,
            book_categories=entity.book_categories or [],
            view_count=entity.view_count,
            first_image=Image(
                id=entity.images[0].id,
                image_path=entity.images[0].image_path,
                image_index=entity.images[0].image_index,
                listing_id=entity.images[0].listing_id
            ) if entity.images else None
        )

    @staticmethod
    def to_list_response(listings: List[ListingEntity], count: int, skip: int, limit: int) -> ListingListResponse:
        """Convertit une liste de ListingEntity en ListingListResponse"""
        return ListingListResponse(
            listings=[ListingMapper.to_summary(listing) for listing in listings],
            count=count,
            skip=skip,
            limit=limit
        )
