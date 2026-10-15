# pylint: disable=protected-access
"""
Tests pour l'objet DamageState
"""
import pytest
from pydantic import ValidationError
from app.core.enums import DamageStateId
from app.schemas.damage_state import DamageState

def test_damage_state_creation_success():
    """Vérifie qu'un objet DamageState est correctement instancié."""
    state_id = DamageStateId.COMME_NEUF
    name = "Comme neuf"
    damage_state = DamageState(id=state_id, name=name)
    assert damage_state.id == state_id
    assert damage_state.name == name

def test_damage_state_invalid_id():
    """Vérifie que l'id doit être un UUID valide."""
    with pytest.raises(ValidationError):
        DamageState(id="invalid-uuid", name="USED")

def test_damage_state_missing_fields():
    """Vérifie que les champs obligatoires sont requis."""
    with pytest.raises(ValidationError):
        DamageState(id=DamageStateId.COMME_NEUF)
    with pytest.raises(ValidationError):
        DamageState(name="USED")
