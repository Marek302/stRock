
import pytest
from uuid import uuid4
from datetime import datetime
from app.services.image_repo import MongoImageRepository
from app.models.image import Image
from app.models.messaging import Conversation
from datetime import datetime

@pytest.fixture
def image_repo(database):
    return MongoImageRepository(db=database)

@pytest.fixture
def conversation_fixture(test_user_id_1, test_user_id_2, test_listing_id):
    return Conversation(
        id=uuid4(),
        participants=[test_user_id_1, test_user_id_2],
        listing_id=test_listing_id,
        created_at=datetime.now()
    )

@pytest.fixture
def image_fixture(conversation_fixture):
    image_id = uuid4()
    return Image(
        id=image_id,
        image_path=f"/{conversation_fixture.id}/{image_id}",
        conversation=conversation_fixture
    )

async def test_insert_and_get_by_id(image_repo: MongoImageRepository, image_fixture: Image):
    await image_repo.insert(image_fixture)

    retrieved_image = await image_repo.get_by_id(image_fixture.id)

    assert retrieved_image is not None
    assert retrieved_image.id == image_fixture.id
    assert retrieved_image.image_path == image_fixture.image_path
    assert retrieved_image.conversation.id == image_fixture.conversation.id


async def test_get_by_id_not_found(image_repo: MongoImageRepository):
    retrieved_image = await image_repo.get_by_id(uuid4())

    assert retrieved_image is None


async def test_delete(image_repo: MongoImageRepository, image_fixture: Image):
    await image_repo.insert(image_fixture)

    await image_repo.delete(image_fixture.id)

    retrieved_image = await image_repo.get_by_id(image_fixture.id)

    assert retrieved_image is None
