"""Exercise multipart uploads and actual image processing without Firebase/network."""
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from app.api.v1.image import router
from app.exception_handlers import add_exception_handlers
from app.services.image_service import ImageService
from app.services.file_service import FileService
from app.services.firebase_token_service import get_firebase_token_service


class ImageUploadTests(unittest.TestCase):
    def test_png_transparency_and_jpeg_upload_and_read(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', PHOTO_SAVE_ROOT=directory), patch('app.services.file_service.NSFW_DETECTION_ENABLED', False):
            image_id = uuid4()
            entity = SimpleNamespace(id=image_id, post_id=uuid4(), image_index=0,
                                     image_path=f'/author/post/{image_id}', post=SimpleNamespace(user_id='author'))
            images = SimpleNamespace(get_by_id=AsyncMock(return_value=entity))
            verifier = SimpleNamespace(verify_id_token=AsyncMock(return_value=SimpleNamespace(uid='author', permissions=[])))
            app = FastAPI()
            app.include_router(router, prefix='/images')
            add_exception_handlers(app)
            app.dependency_overrides[ImageService.get_image_service] = lambda: images
            app.dependency_overrides[get_firebase_token_service] = lambda: verifier
            with TestClient(app) as client:
                for mode, fmt in [('RGBA', 'PNG'), ('LA', 'PNG'), ('RGB', 'JPEG'), ('RGBA', 'WEBP')]:
                    with self.subTest(mode=mode, format=fmt):
                        content = io.BytesIO()
                        Image.new(mode, (20, 20)).save(content, format=fmt)
                        response = client.put(f'/images/{image_id}', headers={'Authorization': 'Bearer test'},
                                              files={'image': (f'capture.{fmt.lower()}', content.getvalue(), f'image/{fmt.lower()}')})
                        self.assertEqual(response.status_code, 204, response.text)
                        saved = Path(directory) / entity.image_path.lstrip('/')
                        with Image.open(saved) as decoded:
                            self.assertEqual(decoded.mode, 'RGB')
                            if mode in ('RGBA', 'LA'):
                                self.assertEqual(decoded.getpixel((0, 0)), (255, 255, 255))
                        loaded = client.get(f'/images/{image_id}')
                        self.assertEqual(loaded.status_code, 200)
                        self.assertTrue(loaded.headers['content-type'].startswith('image/'))
