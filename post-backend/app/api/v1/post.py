"""

Routes pour les publications

"""
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.firebase_user_token import FirebaseUserToken
import app.schemas.summary.post_list_response as postListResponse
import app.schemas.post as post
from app.schemas.filters.post_filters import PostFilters, get_post_filters
from app.services.post_service import PostService
from app.mappers.post_mapper import PostMapper
from app.schemas.create.post_create import PostCreate
from app.schemas.summary.post_location import PostLocation
from app.core.security import with_claims, optional_with_claims
from app.services.messaging_service import MessagingService

router = APIRouter(redirect_slashes=False)

@router.get("")
async def get_all_posts(
    filters: PostFilters = Depends(get_post_filters),
    service: PostService = Depends(PostService.get_post_service)
):
    """Récupère tous les publications avec pagination et filtres optionnels"""
    results = service.list_all(**filters.model_dump())

    return PostMapper.to_list_response(
        posts=results,
        count=len(results),
        skip=filters.skip,
        limit=filters.limit
    )

@router.get("/locations", response_model=list[PostLocation])
async def get_post_locations(
    service: PostService = Depends(PostService.get_post_service)
):
    """Liste tous les posts avec uniquement leur ID, latitude et longitude."""
    return service.list_locations()


@router.post("", status_code=201)
async def create_post(
    post: PostCreate,
    service: PostService = Depends(PostService.get_post_service),
    token: FirebaseUserToken = Depends(with_claims(["post:create:self"]))
):
    """Crée une nouvelle publication"""
    new_post = service.create(post=post, user_id=token.uid)
    schema = PostMapper.to_schema(new_post)
    return {
        "success": True,
        "post": schema,
        "message": "Publication créé avec succès"
    }

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    service: PostService = Depends(PostService.get_post_service),
    messaging: MessagingService = Depends(MessagingService.get_messaging_service),
    auth: Tuple[str, FirebaseUserToken] = Depends(with_claims(["post:delete:self"], decode=False))
):
    """Supprime une publication"""
    token = auth[1]
    encoded_bearer=auth[0]
    post_entity = service.get_by_id(post_id=post_id)
    if post_entity.user_id != token.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not own the post with id: {post_id}"
            )
    await messaging.delete_by_post_id(post_id=post_id,
                                   encoded_token=encoded_bearer)
    service.delete_by_id(entity=post_entity)

@router.get("/user/{user_id}")
async def get_posts_by_user(
    user_id: str,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(
        postListResponse.MAX_LIST_COUNT,
        ge=postListResponse.MIN_LIST_COUNT,
        le=postListResponse.MAX_LIST_COUNT,
        description="Nombre max d'éléments à retourner"
    ),
    service: PostService = Depends(PostService.get_post_service)
):
    """Récupère tous les posts d'un utilisateur avec pagination"""
    results = service.get_by_user(user_id, skip, limit)
    return PostMapper.to_list_response(
        posts=results,
        count=len(results),
        skip=skip,
        limit=limit
    )


@router.get("/{post_id}")
async def get_post(
    post_id: str,
    service: PostService = Depends(PostService.get_post_service),
    token: FirebaseUserToken | None = Depends(optional_with_claims(["post:read:self"]))
):
    """Récupère un post par ID. Incrémente view_count si l'utilisateur authentifié n'est pas le vendeur (une fois par user)."""
    post_entity = service.get_by_id(post_id)
    if token is not None and token.uid != post_entity.user_id:
        service._record_view(post_id=post_id, user_id=token.uid)
    post_entity = service.get_by_id(post_id)
    return PostMapper.to_schema(post_entity)

