# pylint: disable=protected-access
"""
Tests pour le PostService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from app.services.post_service import PostService

@pytest.mark.asyncio
async def test_get_post_service():
    """
    Teste que l'on récupère bien une instance de PostService
    """
    session_mock = AsyncMock()
    service = await PostService.get_post_service(session_mock)
    assert isinstance(service, PostService)
    assert service.session == session_mock


def test_record_view_increments_once_for_new_view(monkeypatch):
    session = MagicMock()
    service = PostService(session)

    post = MagicMock()
    post.id = "post-1"
    post.view_count = 0

    nested = MagicMock()
    nested.__enter__.return_value = None
    nested.__exit__.return_value = False
    session.begin_nested.return_value = nested

    monkeypatch.setattr(service, "get_by_id", lambda _id: post)
    saved = {"called": False}

    def _save(entity):
      saved["called"] = True
      return entity
    monkeypatch.setattr(service, "save", _save)

    created = service._record_view("post-1", "u" * 28)
    assert created is True
    assert post.view_count == 1
    assert saved["called"] is True


def test_record_view_returns_false_on_duplicate_view(monkeypatch):
    session = MagicMock()
    service = PostService(session)

    post = MagicMock()
    post.id = "post-1"
    post.view_count = 2

    nested = MagicMock()
    nested.__enter__.return_value = None
    nested.__exit__.return_value = False
    session.begin_nested.return_value = nested
    session.add.side_effect = IntegrityError("dup", None, None)

    monkeypatch.setattr(service, "get_by_id", lambda _id: post)
    save_spy = MagicMock()
    monkeypatch.setattr(service, "save", save_spy)

    created = service._record_view("post-1", "u" * 28)
    assert created is False
    assert post.view_count == 2
    save_spy.assert_not_called()


def test_update_user_reputation_returns_rowcount_and_commits():
    session = MagicMock()
    result = MagicMock()
    result.rowcount = 3
    session.exec.return_value = result
    service = PostService(session)

    updated = service.update_user_reputation("v" * 28, 8)
    assert updated == 3
    session.exec.assert_called_once()
    session.commit.assert_called_once()
