"""
Enumerations pour les états et offres
"""
from enum import Enum

class DamageStateId(str, Enum):
    """Valeurs permises"""
    COMME_NEUF = '5c8a7b3c-9f13-485d-8b2a-2feed9a8e4a1'
    ACCEPTABLE = 'a3359c1b-d8f7-4b2e-b4af-3d1e510bf9c9'
    ENDOMMAGE = '1b4e0f6a-6b5c-4fd7-9456-2b1f2ad2ef7d'

class SoldStateId(str, Enum):
    """Valeurs permises"""
    AVAILABLE = '26fbcfa4-e63e-4666-8458-c544dff205c0'
    SOLD = '5735ce44-3b31-4058-8a1b-4c834c1fd984'
    PENDING = 'd6a25ebd-eb7f-43b0-a8a9-3a95ebb532ed'
    DRAFT = 'd8a683fb-f74a-41ee-af5a-59bc574a7b15'

class ShippingOfferId(str, Enum):
    """Valeurs permises"""
    SHIP = '1345bd31-fff5-489f-af26-1046f961a2ee'
    LOCAL_MEET = '1ca8f728-8dc2-45a3-8243-30c2785f9a6d'
    MEET_AT_UNIVERSITY = '2d60bda0-f220-4cf5-8ba2-42c162707abe'
