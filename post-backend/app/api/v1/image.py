"""

Routes pour les images

"""
import uuid
from fastapi.responses import FileResponse, Response
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.core.security import with_claims
from app.models.image_entity import ImageEntity
from app.schemas.firebase_user_token import FirebaseUserToken
from app.services.file_service import FileService
from app.services.image_service import ImageService
from app.services.nsfw_detector import NSFW_DETECTION_ENABLED, NSFW_THRESHOLD

router = APIRouter(redirect_slashes=False)

@router.put("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_listing_image(
    image_id: uuid.UUID,
    image: UploadFile = File(...),
    image_service: ImageService = Depends(ImageService.get_image_service),
    file_service: FileService = Depends(FileService.get_file_service),
    token: FirebaseUserToken = Depends(with_claims(["listing:update:self"]))
) -> Response:
    """Upload une photo pour un listing. En-têtes de debug : X-NSFW-Probability, X-NSFW-Threshold, X-NSFW-Detection-Enabled."""
    image_entity: ImageEntity = await image_service.get_by_id(image_id=image_id)
    if image_entity.listing.vendor_id != token.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own the listing attached to this image."
            )
    content = await image.read()
    _path, nsfw_prob = await file_service.save_file(photo=content, image_id=image_id)
    headers = {
        "X-NSFW-Detection-Enabled": "1" if NSFW_DETECTION_ENABLED else "0",
        "X-NSFW-Threshold": str(NSFW_THRESHOLD),
    }
    if nsfw_prob is not None:
        headers["X-NSFW-Probability"] = f"{nsfw_prob:.4f}"
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

@router.get("/{image_id}", status_code=status.HTTP_200_OK)
async def get_image_by_id(
    image_id: uuid.UUID,
    file_service: FileService = Depends(FileService.get_file_service)
    ) -> FileResponse:
    """Récupère une photo de listing par son nom de fichier"""
    path, image_entity, extension = await file_service.get_file(image_id=image_id)
    media_type = f"image/{extension}"
    return FileResponse(
            path,
            media_type=media_type,
            headers={
                "X-Image-Index": str(image_entity.image_index),
                "X-Listing-ID": str(image_entity.listing_id)
            }
        )
    