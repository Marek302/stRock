"""
Fichier de la classe de données FirebaseUserToken
"""
import time
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class FirebaseUserToken():
    """Représente le contenu décodé d'un ID Token Firebase."""
    uid: str
    email: str
    name: str
    picture: str
    role: str
    permissions: List[str]
    email_verified: bool
    sign_in_provider: str
    
    iat: int
    exp: int
    auth_time: int
    iss: str
    aud: str

    @classmethod
    def from_decoded_dict(cls, data: Dict[str, Any]):
        """Factory pour créer l'objet à partir du dictionnaire décodé."""
        firebase_data = data.get("firebase", {})
        
        return cls(
            uid=data.get("sub"),
            email=data.get("email"),
            name=data.get("name"),
            picture=data.get("picture"),
            role=data.get("role"),
            permissions=data.get("permissions", []),
            email_verified=data.get("email_verified", False),
            sign_in_provider=firebase_data.get("sign_in_provider"),
            iat=data.get("iat"),
            exp=data.get("exp"),
            auth_time=data.get("auth_time"),
            iss=data.get("iss"),
            aud=data.get("aud")
        )

    @property
    def is_expired(self) -> bool:
        """Regarder si le token est expiré"""
        return time.time() > self.exp