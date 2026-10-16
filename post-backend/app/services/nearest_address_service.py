"""Recherche une adresse proche pour les posts sans adresse enregistrée."""
import asyncio
import os
import re
import time
from collections import OrderedDict

import httpx


COORDINATE_LABEL = re.compile(r"lat:\s*-?\d+(?:\.\d+)?,\s*lon:\s*-?\d+(?:\.\d+)?", re.I)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = os.getenv("NOMINATIM_USER_AGENT", "stRock/1.0 (Saint-Roch community map)")


def has_saved_address(location: str | None) -> bool:
    return bool(location and location.strip() and not COORDINATE_LABEL.fullmatch(location.strip()))


def format_nearest_address(result: dict) -> str | None:
    details = result.get("address") or {}
    road = next((details.get(key) for key in ("road", "pedestrian", "footway", "street")
                 if details.get(key)), None)
    number = details.get("house_number")
    city = next((details.get(key) for key in ("city", "town", "village", "municipality")
                 if details.get(key)), None)
    street = " ".join(part for part in (number, road) if part)
    address = ", ".join(part for part in (street, city) if part) if street else ""
    if not address:
        address = (result.get("display_name") or "").strip()
    return address[:256] or None


class NearestAddressService:
    """Cache les résultats et limite Nominatim à une requête par seconde."""

    _lock = asyncio.Lock()
    _next_request_at = 0.0
    _cache: OrderedDict[tuple[float, float], str] = OrderedDict()

    @classmethod
    async def lookup(cls, latitude: float, longitude: float) -> str | None:
        key = (round(latitude, 6), round(longitude, 6))
        async with cls._lock:
            if key in cls._cache:
                cls._cache.move_to_end(key)
                return cls._cache[key]

            wait = cls._next_request_at - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            cls._next_request_at = time.monotonic() + 1.1

            async with httpx.AsyncClient(timeout=8, headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "fr-CA,fr",
            }) as client:
                response = await client.get(NOMINATIM_URL, params={
                    "format": "jsonv2",
                    "lat": latitude,
                    "lon": longitude,
                    "zoom": 18,
                    "addressdetails": 1,
                    "layer": "address",
                })
                response.raise_for_status()
                address = format_nearest_address(response.json())

            if address:
                cls._cache[key] = address
                if len(cls._cache) > 512:
                    cls._cache.popitem(last=False)
            return address
