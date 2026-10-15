# pylint: disable=protected-access
from typing import List
from uuid import UUID, uuid4
from dataclasses import asdict
from pathlib import Path
import jwt
import pytest
from app.core.enums import DamageStateId, ShippingOfferId, SoldStateId
from app.models.damage_state_entity import DamageStateEntity
from app.models.image_entity import ImageEntity
from app.models.listing_entity import ListingEntity
from app.models.shipping_offer_entity import ShippingOfferEntity
from app.models.sold_state_entity import SoldStateEntity
from app.schemas.firebase_user_token import FirebaseUserToken


SECRET_KEY = "super-long-testing-secret-key-to-suppress-warnings"
ALGORITHM = "HS256"
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"

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

def insert_listing(db_session, image_count, vendor_id, entities, **overrides) -> List[ImageEntity]:
    """Insère un listing en base en utilisant les valeurs par défaut clés."""
    listing_id = uuid4()
    images = []

    for i in range(image_count):
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
        "seller_rep": overrides.get("seller_rep", 5),
        "buyer": overrides.get("buyer"),
        "images": images
    }
    listing = ListingEntity(**data)
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return images


def test_insert_and_get_valid_images(client, db_session, reference_entities):
    user = get_mock_firebase_user()
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"]
    }
    file_path_jpg = TEST_IMAGES_DIR / "test-jpg.jpg"
    file_path_webp = TEST_IMAGES_DIR / "test-webp.webp"

    image_count=2
    images = insert_listing(
        image_count=image_count,
        db_session=db_session,
        vendor_id=user.uid,
        entities=states,
        location="Québec",
        seller_rep=4
    )

    with open(file_path_jpg, "rb") as f1, open(file_path_webp, "rb") as f2:

        test_files = [
            ("test-jpg.jpg", f1, "image/jpeg"),
            ("test-webp.webp", f2, "image/webp"),
        ]

        for image, (filename, fileobj, content_type) in zip(images, test_files):

            response = client.put(
                f"/api/v1/images/{image.id}",
                files={"image": (filename, fileobj, content_type)},
                headers={"Authorization": "Bearer " + MOCK_JWT}
            )
            assert response.status_code == 204

            response = client.get(
                f"/api/v1/images/{image.id}",
                headers={"Authorization": "Bearer " + MOCK_JWT}
            )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("image/")
            assert response.headers["X-Image-Index"] == str(image.image_index)
            assert response.headers["X-Listing-ID"] == str(image.listing_id)
            assert response.content
        assert len(response.content) > 0

def test_insert_invalid_images(client, db_session, reference_entities):
    user = get_mock_firebase_user()
    states = {
        "damage": reference_entities["damage"]["comme_neuf"],
        "sold": reference_entities["sold"]["available"],
        "shipping": reference_entities["shipping"]["ship"]
    }
    file_path_bad_bytes = TEST_IMAGES_DIR / "test-not_an_image.png"
    file_path_transparency = TEST_IMAGES_DIR / "test-png.png"

    image_count=2
    images = insert_listing(
        image_count=image_count,
        db_session=db_session,
        vendor_id=user.uid,
        entities=states,
        location="Québec",
        seller_rep=4
    )

    with open(file_path_bad_bytes, "rb") as f1, open(file_path_transparency, "rb") as f2:

        response = client.put(
            f"/api/v1/images/{images[0].id}",
            files={"image": ("test-not_an_image.png", f1, "image/png")},
            headers={"Authorization": "Bearer " + MOCK_JWT}
        )

        assert response.status_code == 422
        assert "Invalid image file or unsupported format." in response.text


        response = client.put(
            f"/api/v1/images/{images[1].id}",
            files={"image": ("test-png.png", f2, "image/png")},
            headers={"Authorization": "Bearer " + MOCK_JWT}
        )

        assert response.status_code == 422
        assert "Transparency is not allowed in uploaded images." in response.text
