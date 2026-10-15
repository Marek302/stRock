# pylint: disable=protected-access
"""

Tests pour l'objet PostEntity

"""

import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.models import post_entity
from app.models.damage_state_entity import DamageStateEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.models.sold_state_entity import SoldStateEntity
from app.models.image_entity import ImageEntity

@pytest.fixture
def valid_states(db_session):
    """Initialise les états requis (damage, shipping, sold) en base de données."""
    damage_state = DamageStateEntity(id=uuid4(), name="USED")
    shipping_offer = ShippingOfferEntity(id=uuid4(), name="SHIP")
    sold_state = SoldStateEntity(id=uuid4(), name="PENDING")

    db_session.add_all([damage_state, shipping_offer, sold_state])
    db_session.commit()
    return damage_state, shipping_offer, sold_state

@pytest.fixture
def valid_post_data(valid_states):
    """Génère un dictionnaire de données valides pour créer un PostEntity."""
    damage_state, shipping_offer, sold_state = valid_states

    image = ImageEntity(image_path="/some/image/path", image_index=0)
    return {
        "user_id": "v" * post_entity.USER_ID_LENGTH,
        "book_id": "b" * post_entity.BOOK_ID_LENGTH,
        "title": "Valid Title",
        "damage_state_id": damage_state.id,
        "sold_state_id": sold_state.id,
        "description": "This is a long enough description.",
        "price": 50.0,
        "shipping_offer_id": shipping_offer.id,
        "location": "Paris",
        "seller_rep": 0,
        "images": [
            image
        ]
    }

def insert_post(db_session, data):
    """Persiste une instance d'PostEntity dans la base de données."""
    post = post_entity.PostEntity(**data)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

def test_post_entity_generates_id(db_session, valid_post_data):
    """Vérifie qu'un UUID est automatiquement généré à la création."""
    post = insert_post(db_session, valid_post_data)
    assert post.id is not None

def test_post_entity_missing_fk_fails(db_session, valid_post_data):
    """Vérifie qu'une erreur d'intégrité est levée si une clé étrangère est invalide."""
    valid_post_data["damage_state_id"] = uuid4()
    with pytest.raises(IntegrityError):
        insert_post(db_session, valid_post_data)

def test_post_entity_relationships_loaded(db_session, valid_post_data, valid_states):
    """Vérifie que les relations (Foreign Keys) sont correctement chargées par SQLAlchemy."""
    damage_state, shipping_offer, sold_state = valid_states
    post = insert_post(db_session, valid_post_data)
    # pylint: disable=no-member
    assert post.damage_state.id == damage_state.id
    # pylint: disable=no-member
    assert post.sold_state.id == sold_state.id
    # pylint: disable=no-member
    assert post.shipping_offer.id == shipping_offer.id
