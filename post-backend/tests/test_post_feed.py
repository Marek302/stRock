"""Contrat public de la liste utilisée par le fil des publications.

Tests autonomes, sans Firebase ni base PostgreSQL externe.
"""
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.api.v1.post import router
from app.core.db import get_session
from app.models.image_entity import ImageEntity
from app.models.post_entity import PostEntity


@pytest.fixture
def feed():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/posts")

        def session_override():
            yield session

        app.dependency_overrides[get_session] = session_override
        with TestClient(app) as client:
            yield client, session
    engine.dispose()


def add_post(session, number, title="Une publication du quartier", location="Saint-Roch", with_image=False):
    post = PostEntity(
        id=UUID(int=number),
        user_id="u" * 28,
        title=title,
        description="Une description complète pour le fil des publications.",
        location=location,
        latitude=46.8145,
        longitude=-71.2235,
    )
    if with_image:
        post.images.append(ImageEntity(id=UUID(int=100 + number), image_path="/test/photo", image_index=0))
    session.add(post)
    session.commit()
    return post


def test_empty_feed(feed):
    client, _ = feed
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    assert response.json() == {"posts": [], "count": 0, "skip": 0, "limit": 20}


def test_feed_contains_description_author_and_first_image(feed):
    client, session = feed
    post = add_post(session, 1, with_image=True)
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    item = payload["posts"][0]
    assert item["id"] == str(post.id)
    assert item["title"] == post.title
    assert item["description"] == post.description
    assert item["user_id"] == post.user_id
    assert item["first_image"]["id"] == str(post.images[0].id)


def test_pagination_is_stable_and_allows_posts_without_images(feed):
    client, session = feed
    for number in (3, 1, 2):
        add_post(session, number)
    pages = [client.get("/api/v1/posts", params={"skip": skip, "limit": 1}).json() for skip in range(4)]
    assert [page["posts"][0]["id"] for page in pages[:3]] == [str(UUID(int=n)) for n in (1, 2, 3)]
    assert all(page["posts"][0]["first_image"] is None for page in pages[:3])
    assert pages[3] == {"posts": [], "count": 0, "skip": 3, "limit": 1}


def test_search_and_location_filters(feed):
    client, session = feed
    expected = add_post(session, 1, title="Un café entre voisins")
    add_post(session, 2, title="Un café ailleurs", location="Limoilou")
    add_post(session, 3, title="Une balade entre voisins")
    response = client.get("/api/v1/posts", params={"search": "CAF", "location": "Saint-Roch"})
    assert response.status_code == 200
    assert [post["id"] for post in response.json()["posts"]] == [str(expected.id)]


def test_exclude_ids_supports_comma_separated_and_repeated_params(feed):
    client, session = feed
    for number in (1, 2, 3, 4):
        add_post(session, number)
    response = client.get("/api/v1/posts", params=[
        ("exclude_post_ids", f"{UUID(int=1)},{UUID(int=2)}"),
        ("exclude_post_ids", str(UUID(int=3))),
    ])
    assert response.status_code == 200
    assert [post["id"] for post in response.json()["posts"]] == [str(UUID(int=4))]


@pytest.mark.parametrize("params", [{"limit": 21}, {"skip": -1}])
def test_invalid_pagination_is_rejected(feed, params):
    client, _ = feed
    assert client.get("/api/v1/posts", params=params).status_code == 422
