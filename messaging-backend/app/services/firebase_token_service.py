"""
Fichier du service FirebaseTokenService
"""
import logging
import os
import time
import httpx
import jwt
from cryptography.x509 import load_pem_x509_certificate
from fastapi import HTTPException, status

from app.schemas.firebase_user_token import FirebaseUserToken

class FirebaseTokenService:
    """
    Service singleton servant à la récupération des clés firebase,
    de son décodage et de la validation. 
    """
    class FirebaseKey:
        """Objet de cache des clées"""
        def __init__(self, keys: dict, expires_at: float):
            self.keys = keys
            self.expires_at = expires_at

    def __init__(self):
        self.project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.certs_url = os.getenv("FIREBASE_CERTS_URL")

        self.issuer = f"https://securetoken.google.com/{self.project_id}"
        self._cache = None

    async def _get_public_keys(self) -> dict:
        """Récupère et met en cache les clés selon le max-age."""
        now = time.time()
        
        if self._cache and now < self._cache.expires_at:
            return self._cache.keys
    
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.certs_url)
            resp.raise_for_status()
            
            cache_control = resp.headers.get("cache-control", "")
            current_max_age = 3600
            for part in cache_control.split(","):
                if "max-age" in part:
                    current_max_age = int(part.split("=")[1])
            
            keys = resp.json()
            self._cache = self.FirebaseKey(keys, now + current_max_age)
            return keys

    async def verify_id_token(self, token: str) -> dict:
        """Valide le token selon toutes les contraintes de l'image."""
        if not self.project_id or not self.certs_url:
            logging.warning(
                "Firebase config missing: FIREBASE_PROJECT_ID=%s, FIREBASE_CERTS_URL=%s",
                "set" if self.project_id else "missing",
                "set" if self.certs_url else "missing",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase configuration missing (FIREBASE_PROJECT_ID, FIREBASE_CERTS_URL)",
            )
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            if header.get("alg") != "RS256":
                raise HTTPException(status_code=401, detail="Invalid algorithm")

            public_keys = await self._get_public_keys()
            if not kid or kid not in public_keys:
                raise HTTPException(status_code=401, detail="Invalid or missing kid")

            cert_pem = public_keys[kid]
            if not isinstance(cert_pem, str):
                raise HTTPException(status_code=401, detail="Invalid public key format")
            cert = load_pem_x509_certificate(cert_pem.encode())
            public_key = cert.public_key()

            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.project_id,
                issuer=self.issuer,
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )

            now = time.time()
            if decoded_token.get("auth_time", 0) > now:
                raise HTTPException(status_code=401, detail="Token used before auth_time")
            
            if not decoded_token.get("sub"):
                raise HTTPException(status_code=401, detail="Subject (uid) is empty")

            return FirebaseUserToken.from_decoded_dict(decoded_token)

        except jwt.PyJWTError as e:
            logging.warning("Token validation failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to validate token"
            ) from e
        
_firebase_service = FirebaseTokenService()
async def get_firebase_token_service():
    """Injecté via Depends() dans FastAPI, conserve le cache."""
    return _firebase_service