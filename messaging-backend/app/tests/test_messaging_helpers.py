from uuid import uuid4

import pytest

from app.services.messaging_service import canonical_pair_key


def test_canonical_pair_key_stable_order():
    listing_id = uuid4()
    a = "Z" * 28
    b = "A" * 28
    user1, user2, pair_key = canonical_pair_key([a, b], listing_id)
    assert user1 == b
    assert user2 == a
    assert pair_key == f"{b}|{a}|{listing_id}"


def test_canonical_pair_key_rejects_invalid_participant_count():
    with pytest.raises(ValueError, match="deux participants"):
        canonical_pair_key(["A" * 28], uuid4())
