# pylint: disable=protected-access
"""

Tests pour l'objet Post

"""

import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.schemas import post
from app.schemas.post import Post
from app.schemas.damage_state import DamageState
from app.schemas.shipping_offer import ShippingOffer
from app.schemas.sold_state import SoldState
from app.core.enums import DamageStateId, SoldStateId, ShippingOfferId
from app.schemas.image import Image

@pytest.fixture
def valid_post_data():
    """Génère un dictionnaire de données complet et valide pour le schéma Post."""
    damage_state = DamageState(id=DamageStateId.COMME_NEUF, name="Comme neuf")
    shipping_offer = ShippingOffer(id=ShippingOfferId.SHIP, name="Ship")
    sold_state = SoldState(id=SoldStateId.AVAILABLE, name="Available")
    post_id = uuid4()

    image = Image(
        id=uuid4(),
        image_index=0,
        post_id=post_id
    )

    return {
        "id": post_id,
        "user_id": "v" * 28,
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

def test_post_creation_success(valid_post_data):
    """Vérifie qu'un objet Post est correctement instancié avec des données valides."""
    Post(**valid_post_data)

def test_post_user_id_invalid_length(valid_post_data):
    """Valide que le user_id respecte strictement la longueur définie (min/max)."""
    valid_post_data["user_id"] = "v" * (post.USER_ID_LENGTH - 1)
    with pytest.raises(ValidationError):
        Post(**valid_post_data)
    valid_post_data["user_id"] = "v" * (post.USER_ID_LENGTH + 1)
    with pytest.raises(ValidationError):
        Post(**valid_post_data)

def test_post_book_id_bounds(valid_post_data):
    """Vérifie que le book_id rejette toute valeur en dehors des limites exactes."""
    for offset in [-1, 1]:
        valid_post_data["book_id"] = "b" * (post.BOOK_ID_LENGTH + offset)
        with pytest.raises(ValidationError):
            Post(**valid_post_data)

def test_post_title_bounds(valid_post_data):
    """Teste les limites de longueur minimale et maximale pour le titre de l'post."""
    valid_post_data["title"] = "x" * (post.TITLE_MIN_LENGTH - 1)
    with pytest.raises(ValidationError):
        Post(**valid_post_data)
    valid_post_data["title"] = "x" * (post.TITLE_MAX_LENGTH + 1)
    with pytest.raises(ValidationError):
        Post(**valid_post_data)

def test_post_description_bounds(valid_post_data):
    """Vérifie que la description respecte la longueur minimale requise."""
    valid_post_data["description"] = "too short"
    with pytest.raises(ValidationError):
        Post(**valid_post_data)

@pytest.mark.parametrize("invalid_price", [-1.0, post.PRICE_MIN_VALUE, post.PRICE_MAX_VALUE])
def test_post_price_out_of_bounds(valid_post_data, invalid_price):
    """Vérifie que le prix est refusé s'il est négatif ou hors des bornes autorisées."""
    valid_post_data["price"] = invalid_price
    with pytest.raises(ValidationError):
        Post(**valid_post_data)
