"""
Fichier de la classe FileService
"""
from pathlib import Path
from typing import Tuple, Optional
import io
import uuid
import logging
import os
import aiofiles
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import inspect
from app.models.image_entity import ImageEntity
from app.services.image_service import ImageService
from app.services.service_exceptions import FileTooBigException, StorageException, NsfwContentException
from app.services.nsfw_detector import NSFW_DETECTION_ENABLED, NSFW_THRESHOLD, get_nsfw_probability
from PIL import Image, UnidentifiedImageError

MAX_FILE_SIZE = 10 * 1024 * 1024 #10MB
SUPPORTED_TYPES = ['png','webp','jpeg','jpg']


class FileService:
    """
    Service servant à la récupération et à 
    l'upload des fichiers. 
    """

    def __init__(self, image_service: ImageService):
        """Initialisation du FileService"""
        self.image_service = image_service
        raw_root = os.getenv("PHOTO_SAVE_ROOT")
        if not raw_root:
            raise RuntimeError("PHOTO_SAVE_ROOT is not set")
        self.storage_root = Path(raw_root)

    @staticmethod
    def init_storage():
        """Initialise le dossier de stockage et vérifie les permissions"""
        path=os.getenv("PHOTO_SAVE_ROOT")
        if not path:
            logging.error("PHOTO_SAVE_ROOT est introuvable dans l'environnement")
            raise ValueError("Variable d'environnement manquante")
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, '.permissions_check')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('check')
            os.remove(test_file)
            logging.info("Storage initialized at %s", path)
        except Exception as e:
            logging.error("Failed to initialize storage at %s: %s", path, e)
            raise RuntimeError(f"Storage directory {path} is not writable.") from e 

    @staticmethod
    async def get_file_service(
        image_service: ImageService = Depends(ImageService.get_image_service),
    ) -> "FileService":
        """Récupération du service"""
        return FileService(image_service)

    @staticmethod
    async def remove_file_from_path(image_path: str) -> None:
        """
        Supprime un fichier d'image en se basant uniquement sur son chemin
        relatif stocké dans l'entité, sans accès à la base de données.
        """
        raw_root = os.getenv("PHOTO_SAVE_ROOT")
        if not raw_root:
            raise RuntimeError("PHOTO_SAVE_ROOT is not set")

        storage_root = Path(raw_root)
        absolute_path = storage_root / image_path.lstrip("/")

        try:
            await run_in_threadpool(os.remove, absolute_path)
        except FileNotFoundError:
            logging.warning("File %s not found during delete", absolute_path)
    
    def _get_extension_from_bytes(self, data: bytes) -> str:
        """Vérifie le type de fichier via ses magic numbers et retourne l'extension"""
        try:
            with Image.open(io.BytesIO(data)) as img:
                extension = img.format.lower()
                if extension not in SUPPORTED_TYPES:
                    raise StorageException(f"Unsupported file type: {extension}. Allowed: {SUPPORTED_TYPES}")
                return extension
        except (UnidentifiedImageError, ValueError, TypeError) as e:
            raise StorageException("Invalid image file or unsupported format.") from e

    def _sanitize_and_compress(self, input_bytes: bytes, extension: str):
        input_stream = io.BytesIO(input_bytes)
        with Image.open(input_stream) as img:
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba = img.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                img = Image.alpha_composite(background, rgba)
            img = img.convert("RGB")
            output_stream = io.BytesIO()
            img.save(output_stream, format=extension.upper(), quality=80, optimize=True)
            return output_stream.getvalue()

    async def _get_image(self, image_id, check_path = True) -> Tuple[ImageEntity, Path]:
        image_entity = await self.image_service.get_by_id(image_id=image_id)
        
        absolute_path = self.storage_root / image_entity.image_path.lstrip("/")
               
        if check_path and not await run_in_threadpool(absolute_path.exists):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested image is currently being processed or has not finished uploading."
            )
        return image_entity, absolute_path

    async def save_file(self, photo: bytes, image_id: uuid.UUID) -> Tuple[str, Optional[float]]:
        """
        Upload du fichier à la bonne place selon le id de l'image.

        Returns:
            (chemin_absolu, probabilité_NSFW ou None si détection désactivée)
        """
        if len(photo) > MAX_FILE_SIZE:
            raise FileTooBigException(
                f"File size {len(photo)} exceeds limit of {MAX_FILE_SIZE} bytes"
            )

        extension = self._get_extension_from_bytes(photo)
        compressed_photo = self._sanitize_and_compress(photo, extension)
        if len(compressed_photo) > MAX_FILE_SIZE:
            raise FileTooBigException(
                f"Compressed file size {len(compressed_photo)} exceeds limit of {MAX_FILE_SIZE} bytes"
            )

        nsfw_prob: Optional[float] = None
        if NSFW_DETECTION_ENABLED:
            nsfw_prob = await run_in_threadpool(get_nsfw_probability, compressed_photo)
            if nsfw_prob >= NSFW_THRESHOLD:
                raise NsfwContentException(
                    "Image content is not allowed. Please upload a different photo."
                )

        _, absolute_path = await self._get_image(image_id=image_id, check_path=False)
        try:
            await run_in_threadpool(os.makedirs, absolute_path.parent, exist_ok=True)
            async with aiofiles.open(absolute_path, mode='wb') as f:
                await f.write(compressed_photo)
            return absolute_path.as_posix(), nsfw_prob
        except StorageException as e:
            raise e
        except Exception as e:
            logging.error("Disk error at %s: %s", absolute_path, e)
            raise StorageException("Failed to save file to server.") from e

    async def get_file(self, image_id: uuid.UUID) -> Tuple[str, ImageEntity, str]:
        """
        Récupération d'une image par son id
        """
        image_entity, absolute_path = await self._get_image(image_id=image_id)

        async with aiofiles.open(absolute_path, mode='rb') as f:
            file = await f.read()

        extension = self._get_extension_from_bytes(file)
            
        return absolute_path.as_posix(), image_entity, extension

        
