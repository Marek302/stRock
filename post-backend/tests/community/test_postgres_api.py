"""Tests HTTP sur une base PostgreSQL initialisée par 01-create.sql.

STROCK_TEST_DATABASE_URL doit désigner une base de test dédiée déjà initialisée.
Firebase et la messagerie sont remplacés; les routes, le stockage et SQL sont réels.
"""
import io
import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine, select
from app.api.v1 import post, image
from app.core.db import get_session
from app.exception_handlers import add_exception_handlers
from app.models.image_entity import ImageEntity
from app.models.post_entity import PostEntity
from app.services.firebase_token_service import get_firebase_token_service
from app.services.messaging_service import MessagingService


@unittest.skipUnless(os.getenv('STROCK_TEST_DATABASE_URL'), 'Base PostgreSQL de test non configurée')
class PostgresApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(os.environ['STROCK_TEST_DATABASE_URL'])
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(self.connection)
        app = FastAPI()
        app.include_router(post.router, prefix='/api/v1/posts')
        app.include_router(image.router, prefix='/api/v1/images')
        add_exception_handlers(app)
        self.messaging = SimpleNamespace(delete_by_post_id=AsyncMock())
        async def verify(token):
            return SimpleNamespace(uid=token, permissions=[])
        app.dependency_overrides[get_session] = lambda: self.session
        app.dependency_overrides[get_firebase_token_service] = lambda: SimpleNamespace(verify_id_token=verify)
        app.dependency_overrides[MessagingService.get_messaging_service] = lambda: self.messaging
        self.client = TestClient(app)
        self.headers = {'Authorization': 'Bearer test-author'}

    def tearDown(self):
        self.client.close()
        self.session.close()
        self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def create(self, **values):
        data = dict(title='Activité de test', description='Détails à rechercher quartier',
                    location='Saint-Roch', latitude=46.81, longitude=-71.22,
                    expiration_hours=24)
        data.update(values)
        if data.get('content_type', 'publication') != 'publication' and 'expiration_hours' not in values:
            data.pop('expiration_hours')
        response = self.client.post('/api/v1/posts', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['post']

    def test_sql_schema_matches_models(self):
        inspector = inspect(self.connection)
        for model in [PostEntity, ImageEntity]:
            columns = {c['name']: c for c in inspector.get_columns(model.__tablename__)}
            self.assertEqual(set(columns), set(model.__table__.columns.keys()))
            for column in model.__table__.columns:
                self.assertEqual(column.nullable, columns[column.name]['nullable'], column.name)
        self.assertNotIn('listing', inspector.get_table_names())

    def test_create_read_search_and_pagination(self):
        created = self.create(location='Saint-Roch', images=[{'image_index': 0}])
        self.assertEqual(datetime.fromisoformat(created['expires_at'].replace('Z','+00:00'))
                         - datetime.fromisoformat(created['created_at'].replace('Z','+00:00')),
                         timedelta(hours=24))
        result = self.client.get(f"/api/v1/posts/{created['id']}")
        self.assertEqual(result.status_code, 200, result.text)
        self.assertNotIn('price', result.json())
        self.assertEqual(len(result.json()['images']), 1)
        for url in ['/api/v1/posts?search=quartier&location=Saint-Roch&limit=1',
                    '/api/v1/posts/user/test-author?limit=1']:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['posts'][0]['id'], created['id'])
        self.assertEqual(self.client.get('/api/v1/posts?skip=999').json()['posts'], [])
        self.assertEqual(self.client.get('/api/v1/posts?limit=21').status_code, 422)
        self.assertEqual(self.client.get('/api/v1/posts/not-a-uuid').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/posts/{uuid4()}').status_code, 404)

    def test_request_validation_matches_database_constraints(self):
        now = datetime.now(timezone.utc).isoformat()
        for values in [dict(price=5), dict(images=[{'image_index': 0}, {'image_index': 0}]),
                       dict(images=[{'image_index': 11}]), dict(longitude=None),
                       dict(latitude=91, longitude=-71),
                       dict(content_type='safety_alert', latitude=None, longitude=None),
                       dict(content_type='event', latitude=46.8, longitude=-71, starts_at=now, ends_at=now),
                       dict(content_type='event', latitude=46.8, longitude=-71, starts_at='2026-10-20T12:00:00', ends_at='2026-10-20T14:00:00')]:
            with self.subTest(values=values):
                data = dict(title='Test', description='Détails', location='Saint-Roch',
                            latitude=46.81, longitude=-71.22, expiration_hours=1)
                data.update(values)
                if data.get('content_type', 'publication') != 'publication' and 'expiration_hours' not in values:
                    data.pop('expiration_hours')
                response = self.client.post('/api/v1/posts', json=data, headers=self.headers)
                self.assertEqual(response.status_code, 422, response.text)
        for values in [dict(title='Test', description='Détails'),
                       dict(title='Test', description='Détails', location='Saint-Roch'),
                       dict(title='Test', description='Détails', latitude=46.81, longitude=-71.22),
                       dict(title='Test', description='Détails', location='   ', latitude=46.81, longitude=-71.22),
                       dict(title='Test', description='Détails', location='Saint-Roch', latitude=46.81, longitude=-71.22),
                       dict(title='Test', description='Détails', location='Saint-Roch', latitude=46.81, longitude=-71.22, expiration_hours=0),
                       dict(title='Test', description='Détails', location='Saint-Roch', latitude=46.81, longitude=-71.22, expiration_hours=241)]:
            with self.subTest(values=values):
                response = self.client.post('/api/v1/posts', json=values, headers=self.headers)
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.post('/api/v1/posts', json={'title':'Test', 'description':'Détails'}).status_code, 401)

    def test_event_and_alert_visibility_expiry_and_closure(self):
        now = datetime.now(timezone.utc)
        event = self.create(content_type='event', latitude=46.81, longitude=-71.22,
                            starts_at=now.isoformat(), ends_at=(now+timedelta(hours=1)).isoformat())
        safety = self.create(content_type='safety_alert', latitude=46.81, longitude=-71.22)
        urban = self.create(content_type='urban_alert', latitude=46.81, longitude=-71.22)
        self.assertEqual(datetime.fromisoformat(safety['expires_at'].replace('Z','+00:00')) - datetime.fromisoformat(safety['created_at'].replace('Z','+00:00')), timedelta(hours=2))
        feed = self.client.get('/api/v1/posts/user/test-author').json()['posts']
        self.assertEqual({p['id'] for p in feed}, {event['id'], urban['id']})
        locations = self.client.get('/api/v1/posts/locations').json()
        self.assertTrue({event['id'], safety['id'], urban['id']} <= {p['id'] for p in locations})
        self.assertTrue(all(set(p)=={'id','latitude','longitude'} for p in locations))
        self.assertEqual(self.client.patch(f"/api/v1/posts/{safety['id']}/close", headers={'Authorization':'Bearer other'}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/posts/{event['id']}/close", headers=self.headers).status_code, 400)
        self.assertEqual(self.client.patch(f"/api/v1/posts/{safety['id']}/close", headers=self.headers).status_code, 200)
        entity = self.session.get(PostEntity, UUID(urban['id']))
        entity.created_at = now-timedelta(hours=3)
        entity.expires_at = now-timedelta(hours=1)
        self.session.add(entity)
        self.session.commit()
        locations = self.client.get('/api/v1/posts/locations').json()
        self.assertNotIn(safety['id'], {p['id'] for p in locations})
        self.assertNotIn(urban['id'], {p['id'] for p in locations})

    def test_image_upload_download_and_delete_cascade(self):
        created = self.create(images=[{'image_index': 0}])
        image_id = created['images'][0]['id']
        output = io.BytesIO()
        Image.new('RGB', (12, 12), 'blue').save(output, format='JPEG')
        url = f'/api/v1/images/{image_id}'
        response = self.client.put(url, headers={'Authorization':'Bearer other'}, files={'image':('test.jpg',output.getvalue(),'image/jpeg')})
        self.assertEqual(response.status_code, 403, response.text)
        response = self.client.put(url, headers=self.headers, files={'image':('test.jpg',output.getvalue(),'image/jpeg')})
        self.assertEqual(response.status_code, 204, response.text)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers['x-post-id'], created['id'])
        self.assertEqual(self.client.delete(f"/api/v1/posts/{created['id']}", headers={'Authorization':'Bearer other'}).status_code, 403)
        response = self.client.delete(f"/api/v1/posts/{created['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 204, response.text)
        self.messaging.delete_by_post_id.assert_awaited_once()
        self.assertEqual(self.client.get(f"/api/v1/posts/{created['id']}").status_code, 404)
        self.assertIsNone(self.session.exec(select(ImageEntity).where(ImageEntity.id==UUID(image_id))).first())

    def test_sql_inserts_default_to_two_hour_alert(self):
        key = uuid4()
        self.connection.execute(text("INSERT INTO post(id,user_id,title,description,content_type,latitude,longitude) VALUES (:id,'test-author','Alerte SQL','Détails','urban_alert',46.81,-71.22)"), {'id':key})
        result = self.client.get(f'/api/v1/posts/{key}')
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        self.assertEqual(datetime.fromisoformat(data['expires_at'].replace('Z','+00:00')) - datetime.fromisoformat(data['created_at'].replace('Z','+00:00')), timedelta(hours=2))
