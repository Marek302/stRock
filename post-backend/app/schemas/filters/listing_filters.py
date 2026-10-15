from typing import List, Optional, Literal
from fastapi import Query
from pydantic import BaseModel, Field
import app.schemas.listing as listing
import app.schemas.summary.listing_list_response as listingListResponse


class ListingFilters(BaseModel):
    """Filtres pour la recherche de listings"""
    skip: int = Field(0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(
        listingListResponse.MAX_LIST_COUNT,
        ge=listingListResponse.MIN_LIST_COUNT,
        le=listingListResponse.MAX_LIST_COUNT,
        description="Nombre max d'éléments à retourner"
    )
    search: Optional[str] = Field(None, description="Rechercher dans le titre")
    min_price: Optional[float] = Field(None, ge=listing.PRICE_MIN_VALUE,
                                       le=listing.PRICE_MAX_VALUE,
                                       description="Prix minimum")
    max_price: Optional[float] = Field(None, ge=listing.PRICE_MIN_VALUE,
                                       le=listing.PRICE_MAX_VALUE,
                                       description="Prix maximum")
    location: Optional[str] = Field(
        None,
        min_length=listing.LOCATION_MIN_LENGTH,
        max_length=listing.LOCATION_MAX_LENGTH,
        description="Filtrer par lieu (ville, quartier, etc.)"
    )
    delivery_offer: Optional[bool] = Field(
        None,
        description="Ne garder que les listings avec livraison disponible"
    )
    is_annoted: Optional[bool] = Field(
        None,
        description="Filtrer par annotation (true/false)"
    )
    min_seller_rep: Optional[int] = Field(
        None,
        ge=listing.SELLER_REP_MIN_LENGTH,
        le=listing.SELLER_REP_MAX_LENGTH,
        description="Réputation minimum du vendeur (0-10 half stars)"
    )
    sort_by_price: Optional[Literal["asc", "desc"]] = Field(
        None,
        description="Tri par prix: asc (croissant) ou desc (décroissant)"
    )
    exclude_listing_ids: Optional[List[str]] = Field(
        None,
        description="Listing IDs to exclude (e.g. for recommendations: wishlist + disliked)",
    )


def get_listing_filters(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        listingListResponse.MAX_LIST_COUNT,
        ge=listingListResponse.MIN_LIST_COUNT,
        le=listingListResponse.MAX_LIST_COUNT,
    ),
    search: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    delivery_offer: Optional[bool] = Query(None),
    is_annoted: Optional[bool] = Query(None),
    min_seller_rep: Optional[int] = Query(None),
    sort_by_price: Optional[Literal["asc", "desc"]] = Query(None),
    exclude_listing_ids: Optional[List[str]] = Query(None, description="Listing IDs to exclude (repeat or comma-separated)"),
) -> ListingFilters:
    """Dependency that builds ListingFilters from query params (supports list for exclude_listing_ids)."""
    # Support comma-separated in first element if client sends one string
    expanded_exclude: Optional[List[str]] = None
    if exclude_listing_ids:
        expanded_exclude = []
        for s in exclude_listing_ids:
            expanded_exclude.extend(x.strip() for x in s.split(",") if x.strip())
    return ListingFilters(
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        location=location,
        delivery_offer=delivery_offer,
        is_annoted=is_annoted,
        min_seller_rep=min_seller_rep,
        sort_by_price=sort_by_price,
        exclude_listing_ids=expanded_exclude,
    )
