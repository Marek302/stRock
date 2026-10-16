"""Tests autonomes du domaine communautaire : python -m unittest discover -s tests/community."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
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
from app.services.service_exceptions import NotFoundException


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
        values = dict(title='Une activité', description='Détails de notre activité',
                      location='Saint-Roch', latitude=46.81, longitude=-71.22,
                      expiration_hours=24)
        values.update(kwargs)
        if values.get('content_type', 'publication') != 'publication' and 'expiration_hours' not in kwargs:
            values.pop('expiration_hours')
        return self.service.create(PostCreate(**values), 'demo-user')

    def test_creation_without_commercial_fields_or_images(self):
        entity = self.create()
        response = self.client.get(f'/posts/{entity.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['images'], [])
        self.assertNotIn('price', response.json())
        with self.assertRaises(ValidationError):
            PostCreate(title='Test', description='Détails', price=12)

    def test_report_is_map_only_with_type_in_locations(self):
        publication = self.create()
        report = self.create(content_type='safety_alert')
        feed_ids = {str(post.id) for post in self.service.list_all()}
        self.assertIn(str(publication.id), feed_ids)
        self.assertNotIn(str(report.id), feed_ids)
        locations = self.client.get('/posts/locations').json()
        marker = next(item for item in locations if item['id'] == str(report.id))
        self.assertEqual(marker['content_type'], 'safety_alert')
        self.assertEqual(marker['latitude'], report.latitude)
        self.assertNotIn(report.id, {post.id for post in self.service.get_by_user('demo-user')})

    def test_invalid_coordinates_and_event_dates(self):
        now = datetime.now(timezone.utc)
        for args in [dict(latitude=None), dict(longitude=None),
                     dict(latitude=91, longitude=-71),
                     dict(content_type='safety_alert', latitude=None, longitude=None),
                     dict(content_type='urban_alert', latitude=None, longitude=None),
                     dict(content_type='event', latitude=46.8, longitude=-71),
                     dict(content_type='event', latitude=46.8, longitude=-71, starts_at=now, ends_at=now)]:
            with self.subTest(args=args), self.assertRaises(ValidationError):
                self.create(**args)

    def test_publication_requires_location(self):
        for args in [dict(location=None), dict(location='   '),
                     dict(latitude=None, longitude=None)]:
            with self.subTest(args=args), self.assertRaises(ValidationError):
                self.create(**args)

    def test_preview_address_uses_saved_location_before_external_lookup(self):
        saved = self.create(location='535 Rue du Roi, Québec')
        coordinates_only = self.create(location='lat: 46.814085, lon: -71.223164',
                                       latitude=46.814085, longitude=-71.223164)

        with patch('app.api.v1.post.NearestAddressService.lookup',
                   new_callable=AsyncMock, return_value='535 Rue du Roi, Québec') as lookup:
            saved_response = self.client.get(f'/posts/{saved.id}/nearest-address')
            self.assertEqual(saved_response.status_code, 200)
            self.assertEqual(saved_response.json(), {
                'address': '535 Rue du Roi, Québec', 'source': 'saved',
            })
            lookup.assert_not_awaited()

            fallback_response = self.client.get(f'/posts/{coordinates_only.id}/nearest-address')
            self.assertEqual(fallback_response.status_code, 200)
            self.assertEqual(fallback_response.json(), {
                'address': '535 Rue du Roi, Québec', 'source': 'openstreetmap',
            })
            lookup.assert_awaited_once_with(46.814085, -71.223164)

    def test_publication_requires_duration_between_one_hour_and_ten_days(self):
        for hours in [None, 0, 241]:
            with self.subTest(hours=hours), self.assertRaises(ValidationError):
                self.create(expiration_hours=hours)
        for hours in [1, 240]:
            with self.subTest(hours=hours):
                post = self.create(expiration_hours=hours)
                self.assertEqual(post.expires_at - post.created_at, timedelta(hours=hours))

    def test_expired_publication_is_hidden_and_deleted(self):
        post = self.create(expiration_hours=1)
        post.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        post.expires_at = post.created_at + timedelta(hours=1)
        self.service.save(post)
        self.assertNotIn(post.id, {item.id for item in self.service.list_all()})
        with self.assertRaises(NotFoundException):
            self.service.get_by_id(post.id)
        self.assertEqual(self.service.delete_expired_publications(), 1)
        self.assertIsNone(self.session.get(PostEntity, post.id))

    def test_visibility_expiration_and_closure(self):
        plain = self.create()
        located = self.create(latitude=46.81, longitude=-71.22)
        now = datetime.now(timezone.utc)
        event = self.create(content_type='event', latitude=46.81, longitude=-71.22, starts_at=now, ends_at=now+timedelta(hours=1))
        safety = self.create(content_type='safety_alert', latitude=46.81, longitude=-71.22)
        urban = self.create(content_type='urban_alert', latitude=46.81, longitude=-71.22)
        self.assertEqual(safety.expires_at - safety.created_at, timedelta(hours=2))
        self.assertEqual({p.id for p in self.service.list_all()}, {plain.id, located.id, event.id, urban.id})
        self.assertEqual({p.id for p in self.service.list_locations()}, {plain.id, located.id, event.id, safety.id, urban.id})
        urban.created_at = now - timedelta(hours=3)
        urban.expires_at = now - timedelta(hours=1)
        self.service.save(urban)
        self.service.close_alert(safety)
        self.assertEqual({p.id for p in self.service.list_locations()}, {plain.id, located.id, event.id})
        response = self.client.get('/posts/locations')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()[0]), {'id', 'latitude', 'longitude', 'content_type'})
        self.assertEqual({p.id for p in self.service.list_all(search='activité')}, {plain.id, located.id, event.id})

    def test_database_rejects_unlocated_safety_alert(self):
        self.session.add(PostEntity(id=uuid4(), user_id='demo', title='Danger', description='Test', content_type='safety_alert'))
        with self.assertRaises(IntegrityError):
            self.session.commit()
        self.session.rollback()


if __name__ == '__main__':
    unittest.main()
