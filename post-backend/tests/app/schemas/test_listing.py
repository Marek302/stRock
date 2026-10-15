# pylint: disable=protected-access
"""

Tests pour l'objet Listing

"""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.schemas import listing
from app.schemas.listing import Listing
from app.schemas.damage_state import DamageState
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.sold_state import SoldState
from app.core.enums import DamageStateId, SoldStateId, ShippingOfferId
from app.schemas.image import Image

@pytest.fixture
def valid_listing_data():
    """Génère un dictionnaire de données complet et valide pour le schéma Listing."""
    damage_state = DamageState(id=DamageStateId.COMME_NEUF, name="Comme neuf")
    shipping_offer = ShippingOffer(id=ShippingOfferId.SHIP, name="Ship")
    sold_state = SoldState(id=SoldStateId.AVAILABLE, name="Available")
    listing_id = uuid4()

    image = Image(
        id=uuid4(), 
        image_index=0,
        listing_id=listing_id
    )

    return {
        "id": listing_id,
        "vendor_id": "v" * 28,
        "book_id": "b" * 12,
        "title": "Valid Title",
        "damage_state": damage_state,
        "sold_state": sold_state,
        "description": "This is a long enough description to pass the minimum length.",
        "price": 50.0,
        "shipping_offer": shipping_offer,
        "location": "Paris",
        "seller_rep": 5,
        "buyer": None,
        "images": [image]
    }

def test_listing_creation_success(valid_listing_data):
    """Vérifie qu'un objet Listing est correctement instancié avec des données valides."""
    Listing(**valid_listing_data)

def test_listing_vendor_id_invalid_length(valid_listing_data):
    """Valide que le vendor_id respecte strictement la longueur définie (min/max)."""
    valid_listing_data["vendor_id"] = "v" * (listing.VENDOR_ID_LENGTH - 1)
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)
    valid_listing_data["vendor_id"] = "v" * (listing.VENDOR_ID_LENGTH + 1)
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)

def test_listing_book_id_bounds(valid_listing_data):
    """Vérifie que le book_id rejette toute valeur en dehors des limites exactes."""
    for offset in [-1, 1]:
        valid_listing_data["book_id"] = "b" * (listing.BOOK_ID_LENGTH + offset)
        with pytest.raises(ValidationError):
            Listing(**valid_listing_data)

def test_listing_title_bounds(valid_listing_data):
    """Teste les limites de longueur minimale et maximale pour le titre de l'listing."""
    valid_listing_data["title"] = "x" * (listing.TITLE_MIN_LENGTH - 1)
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)
    valid_listing_data["title"] = "x" * (listing.TITLE_MAX_LENGTH + 1)
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)

def test_listing_description_bounds(valid_listing_data):
    """Vérifie que la description respecte la longueur minimale requise."""
    valid_listing_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)

@pytest.mark.parametrize("invalid_price", [-1.0, listing.PRICE_MIN_VALUE, listing.PRICE_MAX_VALUE])
def test_listing_price_out_of_bounds(valid_listing_data, invalid_price):
    """Vérifie que le prix est refusé s'il est négatif ou hors des bornes autorisées."""
    valid_listing_data["price"] = invalid_price
    with pytest.raises(ValidationError):
        Listing(**valid_listing_data)
