# pylint: disable=protected-access
"""
Tests pour l'objet SoldState
"""
import pytest
from pydantic import ValidationError
from app.core.enums import SoldStateId
from app.schemas.sold_state import SoldState

def test_sold_state_creation_success():
    """Vérifie qu'un objet SoldState est correctement instancié."""
    state_id = SoldStateId.AVAILABLE
    name = "Available"
    sold_state = SoldState(id=state_id, name=name)
    assert sold_state.id == state_id
    assert sold_state.name == name

def test_sold_state_invalid_id():
    """Vérifie que l'id doit être un UUID valide."""
    with pytest.raises(ValidationError):
        SoldState(id="invalid-uuid", name="PENDING")

def test_sold_state_missing_fields():
    """Vérifie que les champs obligatoires sont requis."""
    with pytest.raises(ValidationError):
        SoldState(id=SoldStateId.AVAILABLE)
    with pytest.raises(ValidationError):
        SoldState(name="PENDING")