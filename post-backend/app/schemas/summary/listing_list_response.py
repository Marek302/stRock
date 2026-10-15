"""
Fichier pour la class ListingListResponse
"""

from typing import List
from pydantic import BaseModel, Field
from app.schemas.summary.listing_response_summary import ListingResponseSummary

MIN_LIST_COUNT = 0
MAX_LIST_COUNT = 20

class ListingListResponse(BaseModel):
    """
    Objet de réponse pour une liste de Listing
    """
    listings: List[ListingResponseSummary]
    count: int = Field(ge=MIN_LIST_COUNT, le=MAX_LIST_COUNT)
    skip: int = Field(ge=0)
    limit: int = Field(ge=MIN_LIST_COUNT, le=MAX_LIST_COUNT)