import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.security import with_claims
from app.schemas.firebase_user_token import FirebaseUserToken
from app.schemas.image import ImageDTO
from app.services.file_service import FileService
from app.services.image_service import ImageService
from app.services.messaging_service import MessagingService
from app.core.deps import get_messaging_service


router = APIRouter(redirect_slashes=False)

@router.post("/{conversation_id}/images", status_code=status.HTTP_201_CREATED)
async def upload_conversation_image(
    conversation_id: uuid.UUID,
    image: UploadFile = File(...),
    image_service: ImageService = Depends(ImageService.get_image_service),
    messaging_service: MessagingService = Depends(get_messaging_service),
    file_service: FileService = Depends(FileService.get_file_service),
    token: FirebaseUserToken = Depends(with_claims([]))
) -> ImageDTO:
    """Upload une photo dans une conversation"""
    conversation = await messaging_service.ensure_conversation_member(conversation_id, token.uid)
    entity = await image_service.create_image(conversation=conversation)
    content = await image.read()
    await file_service.save_file(photo=content, image=entity)
    return ImageDTO(id=entity.id, image_path=entity.image_path)  

@router.get("/{conversation_id}/{image_id}", status_code=status.HTTP_200_OK)
async def get_image_by_id(
    image_id: uuid.UUID,
    file_service: FileService = Depends(FileService.get_file_service),
    token: FirebaseUserToken = Depends(with_claims([]))
    ) -> FileResponse:
    """Récupère une photo de listing par son nom de fichier"""
    path, image_entity, extension = await file_service.get_file(image_id=image_id)
    if token.uid not in image_entity.conversation.participants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own the conversation attached to this image."
            )
    media_type = f"image/{extension}"
    return FileResponse(
            path,
            media_type=media_type,
            headers={
                "X-Image-ID": str(image_entity.id),
                "X-Conversation-ID": str(image_entity.conversation.id)
            }
        )