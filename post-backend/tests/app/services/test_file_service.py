# pylint: disable=protected-access
"""
Tests pour le FileService
"""
import uuid
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from app.models.image_entity import ImageEntity
from app.services.file_service import FileService
from app.services.service_exceptions import FileTooBigException, NotFoundException, StorageException

TEST_SAVE_ROOT = "/tmp/test_photos"

@pytest.mark.asyncio
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

@pytest.mark.asyncio
async def test_init_storage_failure():
    """
    Teste que le dossier de stockage n'est pas accessible en écriture
    """
    with patch('os.makedirs', side_effect=OSError("Permission denied")) as mock_makedirs, \
         patch('os.getenv', return_value=TEST_SAVE_ROOT):
        with pytest.raises(RuntimeError):
            FileService.init_storage()
        mock_makedirs.assert_called_once_with(TEST_SAVE_ROOT, exist_ok=True)

@pytest.mark.asyncio
async def test_save_file_too_big():
    """
    Teste qu'un fichier trop gros ne peut pas être sauvegardé
    """
    image_service_mock = AsyncMock()
    with patch('os.getenv', return_value=TEST_SAVE_ROOT):
        file_service = FileService(image_service_mock)
    
    with pytest.raises(FileTooBigException):
        await file_service.save_file(b'a' * (10 * 1024 * 1024 + 1), uuid.uuid4())

@pytest.mark.asyncio
@patch('aiofiles.open')
@patch('app.services.file_service.get_nsfw_probability', return_value=0.01)
@patch('app.services.file_service.run_in_threadpool', new_callable=AsyncMock)
async def test_save_file_success(mock_run_in_threadpool, _mock_nsfw, mock_aiofiles_open):
    """
    Teste que la sauvegarde d'un fichier fonctionne
    """
    async def threadpool_side_effect(func, *args, **kwargs):
        return func(*args, **kwargs)
    mock_run_in_threadpool.side_effect = threadpool_side_effect

    image_service_mock = AsyncMock()
    image_entity_mock = MagicMock()
    image_entity_mock.image_path = "tests/test_images/test-jpg.jpg"
    image_entity_mock.listing_id = uuid.uuid4()
    image_service_mock.get_by_id.return_value = image_entity_mock
    
    mock_file_handle = AsyncMock()
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_file_handle)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_aiofiles_open.return_value = mock_context_manager
    
    with patch('os.getenv', return_value=TEST_SAVE_ROOT):
        file_service = FileService(image_service_mock)

    photo_bytes = None
    path = os.path.join(os.getcwd(), "tests/test_images/test-jpg.jpg")
    print(path)
    with open(path, "rb") as f:
        photo_bytes = f.read()
        f.close()

    image_id = uuid.uuid4()
    
    result_path, nsfw_prob = await file_service.save_file(photo_bytes, image_id)
    
    image_service_mock.get_by_id.assert_called_once_with(image_id=image_id)
    expected_path = Path(TEST_SAVE_ROOT) / Path(image_entity_mock.image_path.lstrip("/"))

    assert result_path == expected_path.as_posix()
    assert nsfw_prob == 0.01
    mock_aiofiles_open.assert_called_with(expected_path, mode='wb')

@pytest.mark.asyncio
async def test_save_file_storage_exception():
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
            await file_service.save_file(b'test', uuid.uuid4())


# ---------------------------------------------------------------------------
# Tests pour FileService.remove_file_from_path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch('app.services.file_service.run_in_threadpool', new_callable=AsyncMock)
async def test_remove_file_from_path_success(mock_run_in_threadpool):
    """
    Teste que remove_file_from_path supprime bien le fichier sur le disque
    à partir d'un chemin relatif.
    """
    async def threadpool_side_effect(func, *args, **kwargs):
        return func(*args, **kwargs)

    mock_run_in_threadpool.side_effect = threadpool_side_effect

    relative_path = "vendor123/listing456/image_from_path"
    expected_abs_path = Path(TEST_SAVE_ROOT) / relative_path

    with patch('os.getenv', return_value=TEST_SAVE_ROOT), \
         patch('os.remove') as mock_os_remove:
        await FileService.remove_file_from_path(relative_path)

    mock_os_remove.assert_called_once_with(expected_abs_path)


@pytest.mark.asyncio
@patch('app.services.file_service.run_in_threadpool', new_callable=AsyncMock)
async def test_remove_file_from_path_file_not_found_is_ignored(mock_run_in_threadpool):
    """
    Teste que remove_file_from_path ignore silencieusement l'absence de fichier.
    """
    async def threadpool_side_effect(func, *args, **kwargs):
        return func(*args, **kwargs)

    mock_run_in_threadpool.side_effect = threadpool_side_effect

    relative_path = "vendor123/listing456/missing_image"
    expected_abs_path = Path(TEST_SAVE_ROOT) / relative_path

    with patch('os.getenv', return_value=TEST_SAVE_ROOT), \
         patch('os.remove', side_effect=FileNotFoundError) as mock_os_remove:
        await FileService.remove_file_from_path(relative_path)

    mock_os_remove.assert_called_once_with(expected_abs_path)
