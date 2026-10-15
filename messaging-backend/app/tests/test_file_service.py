# pylint: disable=protected-access
"""
Tests pour le FileService
"""
from datetime import datetime
import uuid
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from app.models.image import Image
from app.models.messaging import Conversation
from app.services.file_service import FileService
from app.services.service_exceptions import FileTooBigException, StorageException

TEST_SAVE_ROOT = "/tmp/test_photos"

@pytest.fixture
def conversation_fixture(test_user_id_1, test_user_id_2, test_listing_id):
    return Conversation(
        id=uuid.uuid4(),
        participants=[test_user_id_1, test_user_id_2],
        listing_id=test_listing_id,
        created_at=datetime.now()
    )

@pytest.fixture
def image_fixture(conversation_fixture):
    image_id = uuid.uuid4()
    return Image(
        id=image_id,
        image_path=f"/{conversation_fixture.id}/{image_id}",
        conversation=conversation_fixture
    )

async def test_init_storage_success():
    """
    Teste que le dossier de stockage est bien créé
    """
    with patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('os.remove') as mock_remove, \
         patch('os.getenv', return_value=TEST_SAVE_ROOT):
        
        FileService.init_storage()

        mock_makedirs.assert_called_once_with(TEST_SAVE_ROOT, exist_ok=True)
        mock_open.assert_called_once_with(os.path.join(TEST_SAVE_ROOT, '.permissions_check'), 'w', encoding='utf-8')
        mock_remove.assert_called_once_with(os.path.join(TEST_SAVE_ROOT, '.permissions_check'))

async def test_init_storage_failure():
    """
    Teste que le dossier de stockage n'est pas accessible en écriture
    """
    with patch('os.makedirs', side_effect=OSError("Permission denied")) as mock_makedirs, \
         patch('os.getenv', return_value=TEST_SAVE_ROOT):
        with pytest.raises(RuntimeError):
            FileService.init_storage()
        mock_makedirs.assert_called_once_with(TEST_SAVE_ROOT, exist_ok=True)

async def test_save_file_too_big(image_fixture):
    """
    Teste qu'un fichier trop gros ne peut pas être sauvegardé
    """
    image_service_mock = AsyncMock()
    with patch('os.getenv', return_value=TEST_SAVE_ROOT):
        file_service = FileService(image_service_mock)
    
    with pytest.raises(FileTooBigException):
        await file_service.save_file(b'a' * (10 * 1024 * 1024 + 1), image_fixture)

@patch('aiofiles.open')
@patch('app.services.file_service.run_in_threadpool', new_callable=AsyncMock)
async def test_save_file_success(mock_run_in_threadpool, mock_aiofiles_open, image_fixture):
    """
    Teste que la sauvegarde d'un fichier fonctionne
    """
    image_service_mock = AsyncMock()
    
    mock_file_handle = AsyncMock()
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_file_handle)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_aiofiles_open.return_value = mock_context_manager
    
    with patch('os.getenv', return_value=TEST_SAVE_ROOT):
        file_service = FileService(image_service_mock)

    path = os.path.join(os.getcwd(), "app/tests/test_images/test-jpg.jpg")
    with open(path, "rb") as f:
        photo_bytes = f.read()

    result_path = await file_service.save_file(photo_bytes, image_fixture)
    
    expected_path = Path(TEST_SAVE_ROOT) / image_fixture.image_path.lstrip("/")
    
    assert result_path == expected_path.as_posix()
    mock_run_in_threadpool.assert_called()
    mock_aiofiles_open.assert_called_with(expected_path, mode='wb')

async def test_save_file_storage_exception(image_fixture):
    """
    Teste que la sauvegarde d'un fichier qui échoue retourne bien une StorageException
    """
    image_service_mock = AsyncMock()
    image_entity_mock = MagicMock()
    image_entity_mock.image_path = "/test/path/image.jpg"
    image_service_mock.get_by_id.return_value = image_entity_mock
    
    with patch('os.getenv', return_value=TEST_SAVE_ROOT):
        file_service = FileService(image_service_mock)
    
    with patch('app.services.file_service.run_in_threadpool', side_effect=Exception("Disk full")):
        with pytest.raises(StorageException):
            await file_service.save_file(b'test', image_fixture)

async def test_remove_file_from_path_success():
    """
    Teste la suppression réussie d'un fichier
    """
    image_path = "/some/path/image.jpg"
    with patch('os.getenv', return_value=TEST_SAVE_ROOT), \
         patch('app.services.file_service.run_in_threadpool', new_callable=AsyncMock) as mock_run:
        await FileService.remove_file_from_path(image_path)
        
        expected_abs_path = Path(TEST_SAVE_ROOT) / image_path.lstrip("/")
        mock_run.assert_called_once_with(os.remove, expected_abs_path)

async def test_remove_file_from_path_not_found():
    """
    Teste la suppression d'un fichier inexistant (ne doit pas lever d'erreur)
    """
    image_path = "/non/existent.jpg"
    with patch('os.getenv', return_value=TEST_SAVE_ROOT), \
         patch('app.services.file_service.run_in_threadpool', side_effect=FileNotFoundError), \
         patch('logging.warning') as mock_log:
        await FileService.remove_file_from_path(image_path)
        
        mock_log.assert_called()

async def test_remove_file_from_path_no_env():
    """
    Teste que remove_file_from_path lève une erreur si la variable d'env est manquante
    """
    with patch('os.getenv', return_value=None):
        with pytest.raises(RuntimeError, match="PHOTO_SAVE_ROOT_MESSAGING is not set"):
            await FileService.remove_file_from_path("some_path")
