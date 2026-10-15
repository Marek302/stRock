# pylint: disable=protected-access
"""
Tests d'intégration pour FileService.remove_file_from_path.

Stratégie :
  - On copie une vraie image dans un répertoire temporaire avant chaque test.
  - On appelle remove_file_from_path avec une variable d'environnement pointant sur ce répertoire.
  - On vérifie que le fichier est supprimé du disque.
  - En cas d'échec, le fixture de nettoyage (autouse) supprime les images
    résiduelles pour ne laisser aucun « junk ».
"""
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.file_service import FileService

# Répertoire source contenant les images de test
TEST_IMAGES_DIR = Path(__file__).parents[2] / "test_images"

# Racine temporaire utilisée par tous les tests de ce fichier
TMP_STORAGE_ROOT = Path("/tmp/test_remove_file_integration")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def cleanup_tmp_storage():
    """
    Garantit que TMP_STORAGE_ROOT est vide avant chaque test et nettoie
    tous les fichiers résiduels (junk) après le test, qu'il réussisse ou non.
    """
    TMP_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    yield  # ← le test s'exécute ici

    # Nettoyage systématique après le test
    if TMP_STORAGE_ROOT.exists():
        shutil.rmtree(TMP_STORAGE_ROOT, ignore_errors=True)


def _copy_source_image(source_filename: str, dest_relative: str) -> Path:
    """
    Copie une image de test vers TMP_STORAGE_ROOT/<dest_relative>.

    Returns:
        Le chemin absolu de la copie.
    """
    source = TEST_IMAGES_DIR / source_filename
    dest = TMP_STORAGE_ROOT / dest_relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


@pytest.mark.asyncio
async def test_remove_file_from_path_deletes_file():
    """
    Cas nominal : remove_file_from_path doit supprimer le fichier du disque.
    """
    relative_path = "vendor_a/listing_b/image_c.jpg"

    # Copie l'image AVANT de tenter la suppression
    copied_file = _copy_source_image("test-jpg.jpg", relative_path)
    assert copied_file.exists(), "Précondition : le fichier doit exister avant remove_file_from_path"

    with patch("os.getenv", return_value=str(TMP_STORAGE_ROOT)):
        await FileService.remove_file_from_path(relative_path)

    # Vérification : le fichier est bien supprimé du disque
    assert not copied_file.exists(), "Le fichier doit être supprimé du disque après remove_file_from_path"


@pytest.mark.asyncio
async def test_remove_file_from_path_file_not_found_is_ignored():
    """
    Si le fichier est introuvable sur le disque, remove_file_from_path ignore l'erreur
    silencieusement.
    """
    relative_path = "vendor_x/listing_y/image_missing.jpg"
    
    # On ne copie pas le fichier.
    missing_file = TMP_STORAGE_ROOT / relative_path
    assert not missing_file.exists()

    with patch("os.getenv", return_value=str(TMP_STORAGE_ROOT)):
        # Ne doit pas lever d'erreur
        await FileService.remove_file_from_path(relative_path)


@pytest.mark.asyncio
async def test_remove_file_from_path_disk_error_bubbles_up():
    """
    Si la suppression du fichier échoue à cause de permissions (OSError),
    l'exception doit remonter (seul FileNotFoundError est ignoré).
    """
    relative_path = "vendor_err/listing_err/image_err.jpg"

    # Copie l'image avant le test
    copied_file = _copy_source_image("test-jpg.jpg", relative_path)
    assert copied_file.exists()

    # Simule une erreur disque lors de la suppression
    def remove_that_fails(path):
        raise OSError(f"Permission denied: {path}")

    with patch("os.getenv", return_value=str(TMP_STORAGE_ROOT)):
        with patch("os.remove", side_effect=remove_that_fails):
            with pytest.raises(OSError):
                await FileService.remove_file_from_path(relative_path)

    # Le fichier doit toujours être là (non supprimé)
    assert copied_file.exists(), "Le fichier doit rester intact si os.remove échoue"


@pytest.mark.asyncio
async def test_remove_file_from_path_webp_also_works():
    """
    Vérifie que remove_file_from_path fonctionne également avec des images WebP.
    """
    relative_path = "vendor_w/listing_w/image_w.webp"

    copied_file = _copy_source_image("test-webp.webp", relative_path)
    assert copied_file.exists()

    with patch("os.getenv", return_value=str(TMP_STORAGE_ROOT)):
        await FileService.remove_file_from_path(relative_path)

    assert not copied_file.exists(), "Le fichier WebP doit être supprimé du disque"
