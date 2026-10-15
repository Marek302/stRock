"""

Routes pour les listings (annonces)

"""
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.firebase_user_token import FirebaseUserToken
import app.schemas.summary.listing_list_response as listingListResponse
import app.schemas.listing as listing
from app.schemas.filters.listing_filters import ListingFilters, get_listing_filters
from app.services.listing_service import ListingService
from app.mappers.listing_mapper import ListingMapper
from app.schemas.create.listing_create import ListingCreate
from app.schemas.update.vendor_reputation_update import VendorReputationUpdate
from app.core.security import with_claims, optional_with_claims
import app.core.enums as enums
from app.services.messaging_service import MessagingService

router = APIRouter(redirect_slashes=False)

@router.get("")
async def get_all_listings(
    filters: ListingFilters = Depends(get_listing_filters),
    service: ListingService = Depends(ListingService.get_listing_service)
):
    """Récupère tous les listings avec pagination et filtres optionnels"""
    results = service.list_all(**filters.model_dump())
    
    return ListingMapper.to_list_response(
        listings=results,
        count=len(results),
        skip=filters.skip,
        limit=filters.limit
    )

@router.post("", status_code=201)
async def create_listing(
    listing: ListingCreate,
    service: ListingService = Depends(ListingService.get_listing_service),
    token: FirebaseUserToken = Depends(with_claims(["listing:create:self"]))
):
    """Crée un nouveau listing"""
    new_listing = service.create(listing=listing, vendor_id=token.uid)
    schema = ListingMapper.to_schema(new_listing)
    return {
        "success": True,
        "listing": schema,
        "message": "Listing créé avec succès"
    }

@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    service: ListingService = Depends(ListingService.get_listing_service),
    messaging: MessagingService = Depends(MessagingService.get_messaging_service),
    auth: Tuple[str, FirebaseUserToken] = Depends(with_claims(["listing:delete:self"], decode=False))
):
    """Supprime un listing"""
    token = auth[1]
    encoded_bearer=auth[0]
    listing_entity = service.get_by_id(listing_id=listing_id)
    if listing_entity.vendor_id != token.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not own the listing with id: {listing_id}"
            )
    await messaging.delete_by_listing_id(listing_id=listing_id, 
                                   encoded_token=encoded_bearer)
    service.delete_by_id(entity=listing_entity)

@router.get("/{listing_id}/sold-status", status_code=200)
async def get_sold_status(
    listing_id: str,
    service: ListingService = Depends(ListingService.get_listing_service)
):
    """Retourne le status de vente d'une annonce"""
    result = service.get_by_id(listing_id=listing_id)
    schema_result = ListingMapper.to_schema(result)
    return {
        "id": schema_result.sold_state.id,
        "status": schema_result.sold_state.name
    }

@router.patch("/{listing_id}/sold", status_code=201)
async def set_sold(listing_id: str,
                   buyer_id: str = Query(min_length=listing.VENDOR_ID_LENGTH, 
                                         max_length=listing.VENDOR_ID_LENGTH),
                   service: ListingService = Depends(ListingService.get_listing_service),
                   messaging_service: MessagingService = Depends(MessagingService.get_messaging_service),
                   auth: Tuple[str, FirebaseUserToken] = Depends(with_claims(["listing:update:self"], decode=False)),
                   ):
    """Met le status de vente à vendu"""
    result = service.get_by_id(listing_id=listing_id)
    token = auth[1]
    encoded_bearer=auth[0]
    if result.vendor_id != token.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not own the listing with id: {listing_id}"
            )
    await messaging_service.get_message_by_listing_and_participant(
        buyer_id=buyer_id, 
        encoded_token=encoded_bearer, 
        listing_id=listing_id)
    result.buyer = buyer_id
    result.sold_state_id = enums.SoldStateId.SOLD
    new_result = service.save(entity=result)
    new_schema = ListingMapper.to_schema(new_result)
    return new_schema


@router.get("/user/{vendor_id}")
async def get_listings_by_user(
    vendor_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(
        listingListResponse.MAX_LIST_COUNT, 
        ge=listingListResponse.MIN_LIST_COUNT, 
        le=listingListResponse.MAX_LIST_COUNT, 
        description="Nombre max d'éléments à retourner"
    ),
    service: ListingService = Depends(ListingService.get_listing_service)
):
    """Récupère tous les listings d'un utilisateur avec pagination"""
    results = service.get_by_vendor(vendor_id, skip, limit)
    return ListingMapper.to_list_response(
        listings=results,
        count=len(results),
        skip=skip,
        limit=limit
    )


@router.patch("/vendor/{vendor_id}/reputation",status_code=200)
async def update_vendor_reputation(
    vendor_id: str,
    body: VendorReputationUpdate,
    service: ListingService = Depends(ListingService.get_listing_service),
    token: FirebaseUserToken = Depends(with_claims(["admin:update:all"]))
):
    """
    Met à jour seller_rep pour tous les listings d'un vendeur.
    Appelé par la Cloud Function quand users/{uid}.vendor_reputation change dans Firestore.
    """
    updated_count = service.update_vendor_reputation(vendor_id, body.seller_rep)
    return {
        "success": True,
        "vendor_id": vendor_id,
        "seller_rep": body.seller_rep,
        "updated_count": updated_count,
    }

@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    service: ListingService = Depends(ListingService.get_listing_service),
    token: FirebaseUserToken | None = Depends(optional_with_claims(["listing:read:self"]))
):
    """Récupère un listing par ID. Incrémente view_count si l'utilisateur authentifié n'est pas le vendeur (une fois par user)."""
    listing_entity = service.get_by_id(listing_id)
    if token is not None and token.uid != listing_entity.vendor_id:
        service._record_view(listing_id=listing_id, user_id=token.uid)
    listing_entity = service.get_by_id(listing_id)
    return ListingMapper.to_schema(listing_entity)

