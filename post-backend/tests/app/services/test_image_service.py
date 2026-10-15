# pylint: disable=protected-access
"""
Tests pour le ImageService
"""
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest


from app.models.image_entity import ImageEntity
from app.services.image_service import ImageService
from app.services.service_exceptions import NotFoundException

@pytest.mark.asyncio
async def test_get_by_id_found():
    """
        Teste que l'on récupère bien une image par son id
    """
    session_mock = MagicMock()
    image_id = uuid.uuid4()
    expected_image = ImageEntity(
        id=image_id, 
        image_path="test/path",
        image_index=0,
        listing_id=uuid.uuid4()
    )
    
    mock_result = MagicMock()
    mock_result.first.return_value = expected_image
    
    session_mock.exec.return_value = mock_result
    
    image_service = ImageService(session_mock)
    
    image = await image_service.get_by_id(image_id)
    
    session_mock.exec.assert_called_once()
    assert image == expected_image
    assert image.id == image_id

@pytest.mark.asyncio
async def test_get_by_id_not_found():
    """
    Teste que l'on récupère bien une exception si l'image n'est pas trouvée
    """
    session_mock = MagicMock()
    image_id = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.first.return_value = None
    session_mock.exec.return_value = mock_result

    image_service = ImageService(session_mock)

    with pytest.raises(NotFoundException):
        await image_service.get_by_id(image_id)
    session_mock.exec.assert_called_once()

@pytest.mark.asyncio
async def test_get_image_service():
    """
    Teste que l'on récupère bien une instance de ImageService
    """
    session_mock = AsyncMock()
    service = await ImageService.get_image_service(session_mock)
    assert isinstance(service, ImageService)
    assert service.session == session_mock

@pytest.mark.asyncio
async def test_delete_entity():
    """
    Teste que delete_entity appelle session.delete puis session.commit
    sur l'entité fournie.
    """
    session_mock = AsyncMock()
    image_service = ImageService(session_mock)

    image_entity = ImageEntity(
        id=uuid.uuid4(),
        image_path="test/path/image.jpg",
        image_index=0,
        listing_id=uuid.uuid4()
    )

    await image_service.delete_entity(image_entity)

    session_mock.delete.assert_called_once_with(image_entity)
    session_mock.commit.assert_called_once()
