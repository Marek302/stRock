import os
from unittest.mock import AsyncMock, patch
import pytest
from uuid import uuid4
from app.models.image_entity import ImageEntity
from app.models.listing_entity import ListingEntity
from app.models.damage_state_entity import DamageStateEntity
from app.models.sold_state_entity import SoldStateEntity
from app.models.shipping_offer_entity import ShippingOfferEntity

@pytest.fixture
def setup_reference_data(db_session):
    damage = DamageStateEntity(id=uuid4(), name="Comme neuf")
    sold = SoldStateEntity(id=uuid4(), name="Available")
    shipping = ShippingOfferEntity(id=uuid4(), name="Ship", delivery_offer=True)
    db_session.add_all([damage, sold, shipping])
    db_session.commit()
    return damage, sold, shipping

@patch("app.core.db.get_session")
def test_image_listener_deletes_file_on_db_delete(mock_get_session, db_session, setup_reference_data, test_app):
    mock_get_session.return_value.__enter__.return_value = db_session
    damage, sold, shipping = setup_reference_data
    
    # Use the test-specific storage root
    storage_root = os.getenv("PHOTO_SAVE_ROOT", ".pytest_cache/test_uploads")
    os.makedirs(storage_root, exist_ok=True)
    
    # Create a listing and an image
    listing_id = uuid4()
    listing = ListingEntity(
        id=listing_id,
        vendor_id="v"*28,
        book_id="BOOK12345678",
        title="Test Listing",
        description="Description " * 5,
        price=10.0,
        damage_state_id=damage.id,
        sold_state_id=sold.id,
        shipping_offer_id=shipping.id,
        location="Montreal"
    )
    db_session.add(listing)
    
    image_id = uuid4()
    rel_path = f"test_vendor/test_listing/{image_id}.jpg"
    image = ImageEntity(
        id=image_id,
        image_path=f"/{rel_path}",
        image_index=0,
        listing_id=listing_id
    )
    db_session.add(image)
    db_session.commit()

    with patch("app.services.file_service.FileService.remove_file_from_path", new_callable=AsyncMock) as mock_remove:
        abs_path = os.path.join(storage_root, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write("dummy data")
        
        assert os.path.exists(abs_path)

        # Now delete the image from DB — the listener fires and deletes the file
        db_session.delete(image)
        db_session.commit()
        mock_remove.assert_awaited_once_with(image.image_path)

@patch("app.core.db.get_session")
def test_image_listener_deletes_files_on_listing_cascade_delete(mock_get_session, db_session, setup_reference_data, test_app):
    mock_get_session.return_value.__enter__.return_value = db_session
    damage, sold, shipping = setup_reference_data
    storage_root = os.getenv("PHOTO_SAVE_ROOT", ".pytest_cache/test_uploads")
    os.makedirs(storage_root, exist_ok=True)
    
    # Create a listing with multiple images
    listing_id = uuid4()
    listing = ListingEntity(
        id=listing_id,
        vendor_id="v"*28,
        book_id="BOOK12345678",
        title="Test Listing Multi",
        description="Description " * 5,
        price=10.0,
        damage_state_id=damage.id,
        sold_state_id=sold.id,
        shipping_offer_id=shipping.id,
        location="Montreal"
    )
    db_session.add(listing)
    
    image_paths = []
    image_paths_db = []
    image_ids = []
    for i in range(3):
        image_id = uuid4()
        image_ids.append(image_id)
        rel_path = f"test_vendor/multi_listing/{image_id}.jpg"
        image = ImageEntity(
            id=image_id,
            image_path=f"/{rel_path}",
            image_index=i,
            listing_id=listing_id
        )
        db_session.add(image)
        image_paths_db.append(image.image_path)
        
        abs_path = os.path.join(storage_root, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(f"dummy data {i}")
        image_paths.append(abs_path)
        
    db_session.commit()

    with patch("app.services.file_service.FileService.remove_file_from_path", new_callable=AsyncMock) as mock_remove:
        # Verify files exist
        for p in image_paths:
            assert os.path.exists(p)

        db_session.delete(listing)
        db_session.commit()
        for ipath in image_paths_db:
            mock_remove.assert_any_call(ipath)
        assert mock_remove.await_count == 3
