"""

Routes pour les publications

"""
from typing import Tuple
from xml.etree import ElementTree
import httpx
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
from app.services.nearest_address_service import NearestAddressService, has_saved_address

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


@router.get("/reverse-geocode")
async def reverse_geocode(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    """Retourne l'adresse canadienne la plus proche du point choisi."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                "https://geocoder.ca/",
                params={
                    "latt": latitude,
                    "longt": longitude,
                    "reverse": 1,
                    "geoit": "XML",
                    "standard": 1,
                },
            )
            response.raise_for_status()
        root = ElementTree.fromstring(response.content)
    except (httpx.HTTPError, ElementTree.ParseError) as exc:
        raise HTTPException(status_code=502, detail="Service de recherche d’adresse indisponible") from exc

    def field(name: str) -> str:
        return (root.findtext(f".//{name}") or "").strip()

    street = " ".join(part for part in (field("stnumber"), field("staddress")) if part)
    street = street or field("NearRoad")
    if not street:
        raise HTTPException(status_code=404, detail="Aucune adresse trouvée pour ce point")
    address = ", ".join(part for part in (street, field("city"), field("prov")) if part)
    return {"address": address[:256]}


@router.get("/{post_id}/nearest-address")
async def get_nearest_post_address(
    post_id: str,
    service: PostService = Depends(PostService.get_post_service),
):
    """Retourne l'adresse enregistrée ou cherche la plus proche pour l'aperçu."""
    entity = service.get_by_id(post_id)
    if has_saved_address(entity.location):
        return {"address": entity.location.strip(), "source": "saved"}
    if entity.latitude is None or entity.longitude is None:
        raise HTTPException(status_code=404, detail="Aucune adresse disponible pour ce post")
    try:
        address = await NearestAddressService.lookup(entity.latitude, entity.longitude)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Service de recherche d’adresse indisponible") from exc
    if not address:
        raise HTTPException(status_code=404, detail="Aucune adresse trouvée pour ce post")
    return {"address": address, "source": "openstreetmap"}


@router.post("", status_code=201)
async def create_post(
    post: PostCreate,
    service: PostService = Depends(PostService.get_post_service),
    token: FirebaseUserToken = Depends(with_claims([]))
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
    auth: Tuple[str, FirebaseUserToken] = Depends(with_claims([], decode=False))
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
    token: FirebaseUserToken | None = Depends(optional_with_claims([]))
):
    """Récupère les détails d'un contenu."""
    return PostMapper.to_schema(service.get_by_id(post_id))


@router.patch("/{post_id}/close")
async def close_alert(
    post_id: str,
    service: PostService = Depends(PostService.get_post_service),
    token: FirebaseUserToken = Depends(with_claims([])),
):
    entity = service.get_by_id(post_id)
    if entity.user_id != token.uid:
        raise HTTPException(status_code=403, detail="Seul l'auteur peut clôturer cette alerte")
    return PostMapper.to_schema(service.close_alert(entity))
