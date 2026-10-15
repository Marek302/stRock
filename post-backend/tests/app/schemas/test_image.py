# pylint: disable=protected-access
"""
Tests pour l'objet Image
"""
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.schemas.image import Image

def test_image_creation_success():
    """Vérifie qu'un objet Image est correctement instancié."""
    image_id = uuid4()
    post_id = uuid4()
    image_index = 0

    image = Image(
        id=image_id,
        image_index=image_index,
        post_id=post_id
    )

    assert image.id == image_id
    assert image.image_index == image_index
    assert image.post_id == post_id

def test_image_invalid_types():
    """Vérifie que les types de données sont respectés."""
    with pytest.raises(ValidationError):
        Image(id="invalid", image_path="path", image_index=0, post_id=uuid4())

    with pytest.raises(ValidationError):
        Image(id=uuid4(), image_path="path", image_index="zero", post_id=uuid4())

    with pytest.raises(ValidationError):
        Image(id=uuid4(), image_path="path", image_index=0, post_id="invalid")

def test_image_missing_fields():
    """Vérifie que les champs obligatoires sont requis."""
    with pytest.raises(ValidationError):
        Image(id=uuid4(), image_path="path", image_index=0)
