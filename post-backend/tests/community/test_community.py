"""Tests autonomes du domaine communautaire : python -m unittest discover -s tests/community."""
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.api.v1.post import router
from app.models.post_entity import PostEntity
from app.schemas.create.post_create import PostCreate
from app.services.post_service import PostService


class CommunityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.service = PostService(self.session)
        app = FastAPI()
        app.include_router(router, prefix='/posts')
        app.dependency_overrides[PostService.get_post_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.session.close()
        self.engine.dispose()

    def create(self, **kwargs):
        return self.service.create(PostCreate(title='Une activité', description='Détails de notre activité', **kwargs), 'demo-user')

    def test_creation_without_commercial_fields_or_images(self):
        entity = self.create()
        response = self.client.get(f'/posts/{entity.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['images'], [])
        self.assertNotIn('price', response.json())
        with self.assertRaises(ValidationError):
            PostCreate(title='Test', description='Détails', price=12)

    def test_invalid_coordinates_and_event_dates(self):
        now = datetime.now(timezone.utc)
        for args in [dict(latitude=46.8), dict(latitude=91, longitude=-71),
                     dict(content_type='safety_alert'), dict(content_type='urban_alert'),
                     dict(content_type='event', latitude=46.8, longitude=-71),
                     dict(content_type='event', latitude=46.8, longitude=-71, starts_at=now, ends_at=now)]:
            with self.subTest(args=args), self.assertRaises(ValidationError):
                self.create(**args)

    def test_visibility_expiration_and_closure(self):
        plain = self.create()
        located = self.create(latitude=46.81, longitude=-71.22)
        now = datetime.now(timezone.utc)
        event = self.create(content_type='event', latitude=46.81, longitude=-71.22, starts_at=now, ends_at=now+timedelta(hours=1))
        safety = self.create(content_type='safety_alert', latitude=46.81, longitude=-71.22)
        urban = self.create(content_type='urban_alert', latitude=46.81, longitude=-71.22)
        self.assertEqual(safety.expires_at - safety.created_at, timedelta(hours=2))
        self.assertEqual({p.id for p in self.service.list_all()}, {plain.id, located.id, event.id, urban.id})
        self.assertEqual({p.id for p in self.service.list_locations()}, {located.id, event.id, safety.id, urban.id})
        urban.created_at = now - timedelta(hours=3)
        urban.expires_at = now - timedelta(hours=1)
        self.service.save(urban)
        self.service.close_alert(safety)
        self.assertEqual({p.id for p in self.service.list_locations()}, {located.id, event.id})
        response = self.client.get('/posts/locations')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()[0]), {'id', 'latitude', 'longitude'})
        self.assertEqual({p.id for p in self.service.list_all(search='activité')}, {plain.id, located.id, event.id})

    def test_database_rejects_unlocated_safety_alert(self):
        self.session.add(PostEntity(id=uuid4(), user_id='demo', title='Danger', description='Test', content_type='safety_alert'))
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()


if __name__ == '__main__':
    unittest.main()
