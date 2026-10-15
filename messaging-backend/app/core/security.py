"""
Définition de l'authentification
"""
from typing import Annotated

from fastapi import Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer

from app.schemas.firebase_user_token import FirebaseUserToken
from app.services.firebase_token_service import (FirebaseTokenService, 
                                                 get_firebase_token_service) 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def with_claims(claims: list[str]):
    """Dépendance pour l'authentification"""
    async def dependency(encoded_bearer: Annotated[str, Depends(oauth2_scheme)],
                  token_service: FirebaseTokenService = Depends(get_firebase_token_service)):
        if not encoded_bearer:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token: FirebaseUserToken = await token_service.verify_id_token(token=encoded_bearer)
        if not all(c in token.permissions for c in claims):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions in {claims}"
            )
        return token
    return dependency

def with_any_claim(claims: list[str]):
    """Dépendance pour l'authentification"""
    async def dependency(encoded_bearer: Annotated[str, Depends(oauth2_scheme)],
                  token_service: FirebaseTokenService = Depends(get_firebase_token_service)):
        if not encoded_bearer:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        token: FirebaseUserToken = await token_service.verify_id_token(token=encoded_bearer)
        if not any(p in claims for p in token.permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing any required permission in {claims}"
            )
        return token
    return dependency

    
