# pylint: disable=protected-access
"""
Tests pour l'objet ShippingOffer
"""
import pytest
from pydantic import ValidationError
from app.core.enums import ShippingOfferId
from app.schemas.shipping_offer import ShippingOffer

def test_shipping_offer_creation_success():
    """Vérifie qu'un objet ShippingOffer est correctement instancié."""
    offer_id = ShippingOfferId.SHIP
    name = "Ship"
    shipping_offer = ShippingOffer(id=offer_id, name=name)
    assert shipping_offer.id == offer_id
    assert shipping_offer.name == name

def test_shipping_offer_invalid_id():
    """Vérifie que l'id doit être un UUID valide."""
    with pytest.raises(ValidationError):
        ShippingOffer(id="invalid-uuid", name="SHIP")

def test_shipping_offer_missing_fields():
    """Vérifie que les champs obligatoires sont requis."""
    with pytest.raises(ValidationError):
        ShippingOffer(id=ShippingOfferId.SHIP)
    with pytest.raises(ValidationError):
        ShippingOffer(name="SHIP")
