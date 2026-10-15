"""
Fichier de la classe VendorReputationUpdate
"""
from pydantic import Field, BaseModel
import app.schemas.listing as listing


class VendorReputationUpdate(BaseModel):
    """
    Corps pour la mise à jour de la réputation de 
    tous les listings d'un vendeur (appelé par Cloud Function).
    """
    seller_rep: int = Field(ge=listing.SELLER_REP_MIN_LENGTH, 
                            le=listing.SELLER_REP_MAX_LENGTH)