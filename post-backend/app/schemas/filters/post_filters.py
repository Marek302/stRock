from typing import List, Optional, Literal
from fastapi import Query
from pydantic import BaseModel, Field
import app.schemas.post as post
import app.schemas.summary.post_list_response as postListResponse

class PostFilters(BaseModel):
    """Filtres pour la recherche de posts"""
    skip: int = Field(0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(
        postListResponse.MAX_LIST_COUNT,
        ge=postListResponse.MIN_LIST_COUNT,
        le=postListResponse.MAX_LIST_COUNT,
        description="Nombre max d'éléments à retourner"
    )
    search: Optional[str] = Field(None, description="Rechercher dans le titre")
    location: Optional[str] = Field(
        None,
        min_length=post.LOCATION_MIN_LENGTH,
        max_length=post.LOCATION_MAX_LENGTH,
        description="Filtrer par lieu (ville, quartier, etc.)"
    )
    exclude_post_ids: Optional[List[str]] = Field(
        None,
        description="Post IDs to exclude (e.g. for recommendations: wishlist + disliked)",
    )


def get_post_filters(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        postListResponse.MAX_LIST_COUNT,
        ge=postListResponse.MIN_LIST_COUNT,
        le=postListResponse.MAX_LIST_COUNT,
    ),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
) -> PostFilters:
    """Dependency that builds PostFilters from query params (supports list for exclude_post_ids)."""
    # Support comma-separated in first element if client sends one string
    expanded_exclude: Optional[List[str]] = None
    if exclude_post_ids:
        expanded_exclude = []
        for s in exclude_post_ids:
            expanded_exclude.extend(x.strip() for x in s.split(",") if x.strip())
    return PostFilters(
        skip=skip,
        limit=limit,
        search=search,
        location=location,
        exclude_post_ids=expanded_exclude,
    )
