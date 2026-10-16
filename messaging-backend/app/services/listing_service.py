from typing import Optional
from uuid import UUID

import httpx
from app.models.listing import Post

LISTING_API_BASE_URL = "http://post-backend:8000"

class ListingService:
    def __init__(self):
        self.listing_api_base_url = LISTING_API_BASE_URL
        if not self.listing_api_base_url:
            raise ValueError("LISTING_API_BASE_URL environment variable not set")

    async def get_by_id(self, listing_id: UUID) -> Optional[Post]:
        url = f"{self.listing_api_base_url}/api/v1/posts/{listing_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return Post.model_validate(response.json())
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()

    @staticmethod
    def get_listing_service():
        return ListingService()
