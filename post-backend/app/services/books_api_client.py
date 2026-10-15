"""
Client to fetch book volume data (e.g. categories) from the Books API.
Used at listing creation to store book_categories for recommendations.
"""
import logging
import os
from typing import List

import httpx

logger = logging.getLogger(__name__)

BOOKS_API_BASE_URL = os.getenv("BOOKS_API_BASE_URL", "").rstrip("/")
BOOKS_API_TIMEOUT = float(os.getenv("BOOKS_API_TIMEOUT", "10"))


def fetch_volume_categories(book_id: str) -> List[str]:
    """
    Fetch categories for a Google Books volume ID from the Books API.
    Returns empty list on any failure (missing config, network error, 404, invalid response).
    """
    if not book_id or not BOOKS_API_BASE_URL:
        if not BOOKS_API_BASE_URL:
            logger.debug("BOOKS_API_BASE_URL not set; skipping book_categories fetch")
        return []
    url = f"{BOOKS_API_BASE_URL}/books/volumes/{book_id}"
    try:
        with httpx.Client(timeout=BOOKS_API_TIMEOUT) as client:
            response = client.get(url)
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            logger.warning("Books API returned %s for volume %s", response.status_code, book_id)
            return []
        data = response.json()
        raw = data.get("categories")
        if isinstance(raw, list):
            return [str(c).strip() for c in raw if c]
        return []
    except Exception as e:
        logger.warning("Failed to fetch book categories for %s: %s", book_id, e)
        return []
