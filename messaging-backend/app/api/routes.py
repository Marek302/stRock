"""
Routes API pour le service de messagerie Rock-On!.
Gere les conversations et les messages entre utilisateurs.
"""

from typing import Tuple
from uuid import UUID

from fastapi import (APIRouter, 
                     Depends, 
                     HTTPException, 
                     Request, 
                     WebSocket, 
                     WebSocketDisconnect, 
                     status,
                     Query)

from app.core.deps import get_messaging_service
from app.core.security import with_claims
from app.models.listing import Post
from app.models.messaging import Conversation
from app.schemas.firebase_user_token import FirebaseUserToken
from app.schemas.messaging import (
    ConversationDTO,
    CreateConversationRequest,
    LastMessageDTO,
    MarkReadResponse,
    MessageDTO,
    SendMessageRequest,
    DeleteConversationsRequest,
)
from app.services.firebase_token_service import get_firebase_token_service
from app.services.listing_service import ListingService
from app.services.messaging_service import (
    ForbiddenError,
    MessagingService,
    NotFoundError,
    ConflictError,
)

# Tous les comptes Firebase connectés ont accès à la messagerie (CONTEXT.md).
# Les services contrôlent ensuite l’appartenance à chaque conversation.
router = APIRouter()


def _has_permissions(token: FirebaseUserToken, claims: list[str]) -> bool:
    return all(c in token.permissions for c in claims)


async def _authenticate_websocket(websocket: WebSocket, claims: list[str]) -> FirebaseUserToken | None:
    auth_header = websocket.headers.get("authorization", "")
    bearer = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    token_value = websocket.query_params.get("token") or bearer

    if not token_value:
        await websocket.close(code=4401, reason="Missing bearer token")
        return None

    token_service = await get_firebase_token_service()
    try:
        token = await token_service.verify_id_token(token=token_value)
    except HTTPException as exc:
        await websocket.close(code=4401, reason=str(exc.detail))
        return None

    if not _has_permissions(token, claims):
        await websocket.close(code=4403, reason="Missing required permissions")
        return None
    return token


def _conversation_to_dto(convo: Conversation, current_user_uid: str) -> ConversationDTO:
    """Construit le DTO avec other_participant_firebase_uid pour l'utilisateur courant."""
    other = next((p for p in convo.participants if p != current_user_uid), convo.participants[0])

    other_firebase_uid = other
    last_dto = None
    if convo.last_message:
        last_dto = LastMessageDTO(
            content=convo.last_message.content,
            sender_uid=convo.last_message.sender_uid,
            timestamp=convo.last_message.timestamp,
        )
    return ConversationDTO(
        id=convo.id,
        participants=convo.participants,
        listing_id=convo.listing_id,
        created_at=convo.created_at,
        last_message=last_dto,
        other_participant_firebase_uid=other_firebase_uid,
    )

@router.get("/profiles/{uid}")
async def get_contact_profile(
    uid: str,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    try:
        profile = await service.repo.get_contact_profile(token.uid, uid)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not profile:
        raise HTTPException(status_code=404, detail="Profil pas encore synchronisé.")
    return profile


@router.get("/conversations/by-listing-and-participant", response_model=ConversationDTO)
async def get_conversation_by_listing_and_participants(
    listing_id: UUID = Query(),
    buyer_id: str = Query(),
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Récupère une conversation par listing id et l'autre participant.
    """
    try:
        convo = await service.get_conversation_by_listing_and_participants(
            listing_id=listing_id,
            participants=[token.uid, buyer_id]
        )
        return _conversation_to_dto(convo, token.uid)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@router.get("/conversations/{listing_id}", response_model=ConversationDTO)
async def get_conversation_for_listing(
    listing_id: UUID,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
    listing_service: ListingService = Depends(ListingService.get_listing_service),
):
    """
    Recupere une conversation existante pour un listing.
    """
    listing: Post = await listing_service.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Annonce introuvable.")

    convo = await service.get_conversation_by_participants(
        participants=[token.uid, listing.user_id], listing_id=listing_id
    )
    if not convo:
        raise HTTPException(
            status_code=404, detail="Conversation not found for this listing."
        )

    return _conversation_to_dto(convo, token.uid)


@router.post("/conversations", response_model=ConversationDTO, status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
    listing_service: ListingService = Depends(ListingService.get_listing_service),
):
    """
    Cree une nouvelle conversation pour un listing.
    """
    listing: Post = await listing_service.get_by_id(body.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Annonce introuvable.")

    try:
        convo = await service.create_conversation(
            participants=[token.uid, listing.user_id],
            listing_id=body.listing_id,
            caller_uid=token.uid,
            caller_firebase_uid=token.uid,
        )
        return _conversation_to_dto(convo, token.uid)
    except ConflictError as e:
        raise HTTPException(
            status_code=409, detail=str(e)
        ) from e


@router.get("/conversations", response_model=list[ConversationDTO])
async def list_conversations(
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Liste toutes les conversations de l'utilisateur actuel.
    Chaque conversation inclut other_participant_firebase_uid si connu (pour marquer comme vendu).
    """
    await service.repo.save_public_profile(token.uid, token.name, token.picture)
    convos = await service.list_user_conversations(token.uid)
    return [_conversation_to_dto(c, token.uid) for c in convos]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageDTO])
async def list_messages(
    conversation_id: UUID,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Liste tous les messages d'une conversation.

    Args:
        conversation_id: UUID de la conversation
        me: UUID de l'utilisateur actuel (depuis header X-User-Id)
        service: Instance du service de messagerie

    Returns:
        Liste des messages tries par timestamp croissant (plus ancien en premier)

    Raises:
        HTTPException: 404 si la conversation n'existe pas, 403 si acces refuse
    """
    try:
        return await service.get_messages(conversation_id, token.uid)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/conversations/{conversation_id}/messages", response_model=MessageDTO)
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    request: Request,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
    listing_service: ListingService = Depends(ListingService.get_listing_service),
):
    """
    Envoie un message dans une conversation.

    Args:
        conversation_id: UUID de la conversation
        body: Requete contenant le contenu du message
        me: UUID de l'utilisateur actuel (depuis header X-User-Id)
        service: Instance du service de messagerie

    Returns:
        Message cree avec son timestamp et ses metadonnees

    Raises:
        HTTPException: 404 si conversation introuvable, 403 si acces refuse,
                      400 si message vide
    """
    try:
        convo = await service.ensure_conversation_member(conversation_id, token.uid)

        article_title = "Nouvelle annonce"
        try:
            listing = await listing_service.get_by_id(convo.listing_id)
            if listing and listing.title:
                article_title = listing.title
        except Exception:
            article_title = "Nouvelle annonce"

        sender_name = (token.name or "Quelqu'un").strip() if token.name else "Quelqu'un"

        message = await service.send_message(
            conversation_id,
            token.uid,
            body.content,
            body.image_ids,
            sender_name=sender_name,
            article_title=article_title,
        )
        await request.app.state.ws_manager.broadcast_message(message)
        return message
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_ws(
    websocket: WebSocket,
    conversation_id: UUID,
):
    token = await _authenticate_websocket(websocket, [])
    if not token:
        return

    service: MessagingService = websocket.app.state.messaging_service
    try:
        await service.ensure_conversation_member(conversation_id, token.uid)
    except NotFoundError:
        await websocket.close(code=4404, reason="Conversation introuvable.")
        return
    except ForbiddenError:
        await websocket.close(code=4403, reason="Acces refuse a cette conversation.")
        return

    manager = websocket.app.state.ws_manager
    await manager.connect(conversation_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(conversation_id, websocket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        await manager.disconnect(conversation_id, websocket)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
   


@router.post("/conversations/{conversation_id}/read", response_model=MarkReadResponse)
async def mark_read(
    conversation_id: UUID,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Marque tous les messages d'une conversation comme lus par l'utilisateur actuel.

    Returns:
        Reponse avec le nombre de messages marques comme lus

    Raises:
        HTTPException: 404 si conversation introuvable, 403 si acces refuse
    """
    try:
        updated = await service.mark_conversation_as_read(conversation_id, token.uid)
        return MarkReadResponse(updated=updated)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/conversations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversations(
    body: DeleteConversationsRequest,
    token: FirebaseUserToken = Depends(with_claims([])),
    service: MessagingService = Depends(get_messaging_service),
):
    """
    Supprime plusieurs conversations pour l'utilisateur actuel.
    """
    for conversation_id in body.conversation_ids:
        try:
            await service.delete_conversation(conversation_id, token.uid)
        except NotFoundError:
            pass
        except ForbiddenError as e:
            raise HTTPException(status_code=403, detail=str(e)) from e
    return

@router.delete("/listing/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_by_listing(
    listing_id: UUID,
    token: FirebaseUserToken = Depends(with_claims([])),
    messaging_service: MessagingService = Depends(get_messaging_service),
    listing_service: ListingService = Depends(ListingService.get_listing_service),
):
    """
    Supprime toutes les conversations d'une annonce pour l'utilisateur actuel.
    """
    listing: Post = await listing_service.get_by_id(listing_id)
    if token.uid != listing.user_id:
        raise HTTPException(status_code=403, detail="Acces refuse a cette annonce.")
    await messaging_service.delete_conversations_by_listing_id(listing_id, token.uid)
    return

