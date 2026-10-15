# pylint: disable=protected-access
"""
Tests pour le ListingService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from app.services.listing_service import ListingService

@pytest.mark.asyncio
async def test_get_listing_service():
    """
    Teste que l'on récupère bien une instance de ListingService
    """
    session_mock = AsyncMock()
    service = await ListingService.get_listing_service(session_mock)
    assert isinstance(service, ListingService)
    assert service.session == session_mock


def test_record_view_increments_once_for_new_view(monkeypatch):
    session = MagicMock()
    service = ListingService(session)

    listing = MagicMock()
    listing.id = "listing-1"
    listing.view_count = 0

    nested = MagicMock()
    nested.__enter__.return_value = None
    nested.__exit__.return_value = False
    session.begin_nested.return_value = nested

    monkeypatch.setattr(service, "get_by_id", lambda _id: listing)
    saved = {"called": False}

    def _save(entity):
      saved["called"] = True
      return entity
    monkeypatch.setattr(service, "save", _save)

    created = service._record_view("listing-1", "u" * 28)
    assert created is True
    assert listing.view_count == 1
    assert saved["called"] is True


def test_record_view_returns_false_on_duplicate_view(monkeypatch):
    session = MagicMock()
    service = ListingService(session)

    listing = MagicMock()
    listing.id = "listing-1"
    listing.view_count = 2

    nested = MagicMock()
    nested.__enter__.return_value = None
    nested.__exit__.return_value = False
    session.begin_nested.return_value = nested
    session.add.side_effect = IntegrityError("dup", None, None)

    monkeypatch.setattr(service, "get_by_id", lambda _id: listing)
    save_spy = MagicMock()
    monkeypatch.setattr(service, "save", save_spy)

    created = service._record_view("listing-1", "u" * 28)
    assert created is False
    assert listing.view_count == 2
    save_spy.assert_not_called()


def test_update_vendor_reputation_returns_rowcount_and_commits():
    session = MagicMock()
    result = MagicMock()
    result.rowcount = 3
    session.exec.return_value = result
    service = ListingService(session)

    updated = service.update_vendor_reputation("v" * 28, 8)
    assert updated == 3
    session.exec.assert_called_once()
    session.commit.assert_called_once()
