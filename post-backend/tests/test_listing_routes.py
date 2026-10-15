# pylint: disable=protected-access
"""
Tests d'intégration pour les routes de l'API Listing.
"""
from uuid import UUID, uuid4
from dataclasses import asdict
import pytest
import jwt

from conftest import ALGORITHM, SECRET_KEY
from app.core.enums import DamageStateId, SoldStateId, ShippingOfferId
from app.models.image_entity import ImageEntity
from app.models.listing_entity import ListingEntity
from app.models.damage_state_entity import DamageStateEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.models.sold_state_entity import SoldStateEntity
from app.schemas.create.image_create import ImageCreate
from app.schemas.create.listing_create import ListingCreate
from app.schemas.firebase_user_token import FirebaseUserToken




@pytest.fixture
def reference_entities(db_session):
    """Crée l'intégralité des états possibles en base de données."""
    
    # 1. Damage States
    damage_entities = {
        "comme_neuf": DamageStateEntity(id=UUID(DamageStateId.COMME_NEUF.value), name="Comme neuf"),
        "acceptable": DamageStateEntity(id=UUID(DamageStateId.ACCEPTABLE.value), name="Acceptable"),
        "endommage": DamageStateEntity(id=UUID(DamageStateId.ENDOMMAGE.value), name="Endommagé"),
    }

    # 2. Sold States
    sold_entities = {
        "available": SoldStateEntity(id=UUID(SoldStateId.AVAILABLE.value), name="Available"),
        "sold": SoldStateEntity(id=UUID(SoldStateId.SOLD.value), name="Sold"),
        "pending": SoldStateEntity(id=UUID(SoldStateId.PENDING.value), name="Pending"),
        "draft": SoldStateEntity(id=UUID(SoldStateId.DRAFT.value), name="Draft"),
    }

    # 3. Shipping Offers
    shipping_entities = {
        "ship": ShippingOfferEntity(
            id=UUID(ShippingOfferId.SHIP.value), name="Ship", delivery_offer=True
        ),
        "local_meet": ShippingOfferEntity(
            id=UUID(ShippingOfferId.LOCAL_MEET.value), name="Meet locally", delivery_offer=False
        ),
        "university": ShippingOfferEntity(
            id=UUID(ShippingOfferId.MEET_AT_UNIVERSITY.value), name="Meet at University", delivery_offer=False
        ),
    }

    # Ajout massif à la session
    all_entities = [
        *damage_entities.values(),
        *sold_entities.values(),
        *shipping_entities.values()
    ]
    
    db_session.add_all(all_entities)
    db_session.commit()

    # Retourne un dictionnaire organisé pour un accès facile dans les tests
    return {
        "damage": damage_entities,
        "sold": sold_entities,
        "shipping": shipping_entities
    }


def insert_listing(db_session, vendor_id, entities, **overrides):
    """Insère un listing en base en utilisant les valeurs par défaut clés."""
    listing_id = uuid4()
    images = []

    for i in range(3):
        image_id = uuid4()
        images.append(ImageEntity(
                id= image_id,
                image_path=f"/{vendor_id}/{listing_id}/{image_id}",
                image_index= i,
                listing_id= listing_id 
            ))
    data = {
        "id": listing_id,
        "vendor_id": vendor_id,
        "book_id": "BOOK12345678",
        "title": "Titre",
        "description": "Description suffisamment longue.",
        "price": 25.0,
        "damage_state_id": entities["damage"].id,
        "sold_state_id": entities["sold"].id,
        "shipping_offer_id": entities["shipping"].id,
        "location": overrides.get("location", "Ville"),
        "is_annoted": overrides.get("is_annoted", False),
        "seller_rep": overrides.get("seller_rep", 5),
        "buyer": overrides.get("buyer"),
        "images": images
    }
    listing = ListingEntity(**data)
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing

def get_mock_firebase_user(uid: str = "v"*28, role: str = "basic_user"):
    return FirebaseUserToken(
        uid=uid,
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.png",
        role=role,
        permissions=[
            "listing:create:self",
            "listing:update:self",
            "listing:read:self",
            "listing:delete:self",
            "admin:update:all" # Si vous testez la route réputation
        ],
        email_verified=True,
        sign_in_provider="google.com",
        iat=1700000000,
        exp=1900000000,
        auth_time=1700000000,
        iss="https://securetoken.google.com/mock",
        aud="mock-project"
    )

MOCK_JWT = jwt.encode(payload=asdict(get_mock_firebase_user()), key=SECRET_KEY, algorithm=ALGORITHM)
MOCK_JWT_OTHER_USER = jwt.encode(payload=asdict(get_mock_firebase_user(uid="b"*28)), 
                                 key=SECRET_KEY, algorithm=ALGORITHM)

def test_get_listings_with_filters(client, db_session, reference_entities):
    """Vérifie la récupération des listings avec des filtres appliqués."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"]
    }
    listing_a = insert_listing(
        db_session,
        vendor_id="g"*28,
        entities=states,
        location="Montreal",
        seller_rep=8,
        is_annoted=True,
    )
    insert_listing(
        db_session,
        vendor_id="v"*28,
        entities=states,
        location="Quebec",
        seller_rep=4,
        is_annoted=False,
    )
    response = client.get(
        "/api/v1/listings",
        params={
            "delivery_offer": True,
            "location": "Montreal",
            "min_seller_rep": 7,
            "is_annoted": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["listings"][0]["id"] == str(listing_a.id)
    assert payload["listings"][0]["seller_rep"] == 8

def test_create_listing_and_get_by_id(client, reference_entities):
    """Vérifie la création d'un listing et sa récupération par ID."""
    entities = reference_entities
    payload = ListingCreate(
        book_id="BOOK00000001",
        title="Nouvelle annonce",
        description= "Une description détaillée.",
        price= 19.99,
        damage_state_id=entities["damage"]["comme_neuf"].id,
        sold_state_id= entities["sold"]["available"].id,
        shipping_offer_id=entities["shipping"]["ship"].id,
        location= "Trois-Rivières",
        seller_rep= 7,
        buyer=None,
        images=[ImageCreate(image_index=0)]
    ).model_dump(mode='json')
    
    print(payload)
    create_resp = client.post("/api/v1/listings", json=payload, headers={
        "Authorization": "Bearer " + MOCK_JWT
        })
    assert create_resp.status_code == 201
    listing = create_resp.json()["listing"]

    get_resp = client.get(f"/api/v1/listings/{listing['id']}")

    assert get_resp.status_code == 200
    assert get_resp.json()["vendor_id"] == get_mock_firebase_user().uid


def test_get_listings_by_user_and_update_reputation(
    client, db_session, reference_entities
):
    """Vérifie la récupération par utilisateur et la mise à jour de la réputation."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"]
    }
    vendor_id = "v" * 28
    listing_one = insert_listing(
        db_session,
        vendor_id=vendor_id,
        entities=states,
        buyer="b"*28,
        seller_rep=6,
    )
    insert_listing(
        db_session,
        vendor_id=vendor_id,
        entities=states,
        seller_rep=6,
        buyer=None
    )

    user_resp = client.get(f"/api/v1/listings/user/{vendor_id}")
    assert user_resp.status_code == 200
    assert user_resp.json()["count"] == 2

    patch_resp = client.patch(
        f"/api/v1/listings/vendor/{vendor_id}/reputation",
        json={"seller_rep": 9},
        headers={"Authorization": "Bearer " + MOCK_JWT}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["updated_count"] == 2

    refreshed = client.get(f"/api/v1/listings/{listing_one.id}")
    assert refreshed.status_code == 200
    assert refreshed.json()["seller_rep"] == 9


def test_get_listing_sold_status(client, reference_entities):
    entities = reference_entities

    payload = ListingCreate(
        book_id="BOOK00000002",
        title="Annonce vendue ?",
        description="Test sold status listing" *2,
        price=29.99,
        damage_state_id=entities["damage"]["comme_neuf"].id,
        sold_state_id=entities["sold"]["available"].id,
        shipping_offer_id=entities["shipping"]["ship"].id,
        location="Québec",
        seller_rep=5,
        buyer=None,
        images=[ImageCreate(image_index=0)]
    ).model_dump(mode="json")

    create_resp = client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": "Bearer " + MOCK_JWT}
    )
    assert create_resp.status_code == 201

    listing_id = create_resp.json()["listing"]["id"]

    response = client.get(f"/api/v1/listings/{listing_id}/sold-status")

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == str(entities["sold"]["available"].id)
    assert body["status"] == entities["sold"]["available"].name


def test_delete_listing_as_owner(client, reference_entities):
    entities = reference_entities

    payload = ListingCreate(
        book_id="BOOK00000003",
        title="Annonce à supprimer",
        description="Delete test listing"*2,
        price=15.00,
        damage_state_id=entities["damage"]["comme_neuf"].id,
        sold_state_id=entities["sold"]["available"].id,
        shipping_offer_id=entities["shipping"]["ship"].id,
        location="Montréal",
        seller_rep=6,
        buyer=None,
        images=[ImageCreate(image_index=0)]
    ).model_dump(mode="json")

    create_resp = client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": "Bearer " + MOCK_JWT}
    )
    assert create_resp.status_code == 201

    listing_id = create_resp.json()["listing"]["id"]

    delete_resp = client.delete(
        f"/api/v1/listings/{listing_id}",
        headers={"Authorization": "Bearer " + MOCK_JWT}
    )

    assert delete_resp.status_code == 204
    
    get_resp = client.get(f"/api/v1/listings/{listing_id}")
    assert get_resp.status_code == 404


def test_delete_listing_not_owner_forbidden(client, reference_entities):
    entities = reference_entities

    payload = ListingCreate(
        book_id="BOOK00000004",
        title="Annonce protégée",
        description="Forbidden delete listing"*2,
        price=10.00,
        damage_state_id=entities["damage"]["comme_neuf"].id,
        sold_state_id=entities["sold"]["available"].id,
        shipping_offer_id=entities["shipping"]["ship"].id,
        location="Sherbrooke",
        seller_rep=3,
        buyer=None,
        images=[ImageCreate(image_index=0)]
    ).model_dump(mode="json")

    create_resp = client.post(
        "/api/v1/listings",
        json=payload,
        headers={"Authorization": "Bearer " + MOCK_JWT}
    )
    assert create_resp.status_code == 201

    listing_id = create_resp.json()["listing"]["id"]

    delete_resp = client.delete(
        f"/api/v1/listings/{listing_id}",
        headers={"Authorization": "Bearer " + MOCK_JWT_OTHER_USER}
    )

    assert delete_resp.status_code == 403
    assert "do not own the listing" in delete_resp.text


# ----- Tests pour GET /listings/{id} et incrément des vues -----

def _mk_jwt(uid: str) -> str:
    """Génère un JWT pour un uid donné."""
    return jwt.encode(
        payload=asdict(get_mock_firebase_user(uid=uid)),
        key=SECRET_KEY,
        algorithm=ALGORITHM
    )


def test_get_listing_without_auth_returns_listing_no_view_increment(
    client, db_session, reference_entities
):
    """Sans auth, le listing est retourné et view_count reste 0."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    listing = insert_listing(
        db_session,
        vendor_id="v" * 28,
        entities=states,
    )
    assert listing.view_count == 0

    resp = client.get(f"/api/v1/listings/{listing.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(listing.id)
    assert data["view_count"] == 0

    # Vérifier en base que view_count n'a pas changé
    db_session.refresh(listing)
    assert listing.view_count == 0


def test_get_listing_with_auth_other_user_increments_view_once(
    client, db_session, reference_entities
):
    """Avec auth (user != vendor), view_count s'incrémente à 1."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    vendor_id = "v" * 28
    viewer_id = "b" * 28
    listing = insert_listing(db_session, vendor_id=vendor_id, entities=states)
    assert listing.view_count == 0

    resp = client.get(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {_mk_jwt(viewer_id)}"},
    )
    assert resp.status_code == 200
    assert resp.json()["view_count"] == 1

    db_session.refresh(listing)
    assert listing.view_count == 1


def test_get_listing_vendor_viewing_own_listing_no_increment(
    client, db_session, reference_entities
):
    """Le vendeur qui consulte sa propre annonce : view_count ne s'incrémente pas."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    vendor_id = "v" * 28
    listing = insert_listing(db_session, vendor_id=vendor_id, entities=states)
    assert listing.view_count == 0

    resp = client.get(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {_mk_jwt(vendor_id)}"},
    )
    assert resp.status_code == 200
    assert resp.json()["view_count"] == 0

    db_session.refresh(listing)
    assert listing.view_count == 0


def test_get_listing_same_user_twice_increments_once(
    client, db_session, reference_entities
):
    """Même user consulte 2 fois : view_count ne s'incrémente qu'une fois."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    vendor_id = "v" * 28
    viewer_id = "c" * 28
    listing = insert_listing(db_session, vendor_id=vendor_id, entities=states)

    for _ in range(2):
        resp = client.get(
            f"/api/v1/listings/{listing.id}",
            headers={"Authorization": f"Bearer {_mk_jwt(viewer_id)}"},
        )
        assert resp.status_code == 200

    assert resp.json()["view_count"] == 1
    db_session.refresh(listing)
    assert listing.view_count == 1


def test_get_listing_two_different_users_increments_twice(
    client, db_session, reference_entities
):
    """Deux users différents consultent : view_count = 2."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    vendor_id = "v" * 28
    listing = insert_listing(db_session, vendor_id=vendor_id, entities=states)

    resp1 = client.get(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {_mk_jwt('a' * 28)}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["view_count"] == 1

    resp2 = client.get(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": f"Bearer {_mk_jwt('b' * 28)}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["view_count"] == 2

    db_session.refresh(listing)
    assert listing.view_count == 2


def test_get_listing_not_found_404(client, reference_entities):
    """ID invalide ou inexistant retourne 404."""
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = client.get(f"/api/v1/listings/{fake_id}")
    assert resp.status_code == 404


def test_get_listing_invalid_uuid_404(client):
    """ID mal formé (non-UUID) retourne 404."""
    resp = client.get("/api/v1/listings/not-a-uuid")
    assert resp.status_code == 404


def test_get_listing_response_includes_view_count_and_full_schema(
    client, db_session, reference_entities
):
    """La réponse contient view_count et les champs attendus."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    listing = insert_listing(
        db_session,
        vendor_id="v" * 28,
        entities=states,
    )

    resp = client.get(f"/api/v1/listings/{listing.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert "view_count" in data
    assert data["view_count"] >= 0
    assert data["id"] == str(listing.id)
    assert data["vendor_id"] == listing.vendor_id
    assert data["title"] == listing.title
    assert data["price"] == listing.price
    assert "images" in data
    assert "damage_state" in data
    assert "sold_state" in data
    assert "shipping_offer" in data


def test_get_listing_with_invalid_token_treated_as_no_auth(
    client, db_session, reference_entities
):
    """Token invalide ou expiré : pas d'auth, view_count reste 0."""
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"],
    }
    listing = insert_listing(
        db_session,
        vendor_id="v" * 28,
        entities=states,
    )

    resp = client.get(
        f"/api/v1/listings/{listing.id}",
        headers={"Authorization": "Bearer invalid-or-expired-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["view_count"] == 0

    db_session.refresh(listing)
    assert listing.view_count == 0
