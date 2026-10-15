import pytest
from unittest.mock import patch
from app.core.db import Settings, get_settings

def test_settings_mongo_uri():
    settings = Settings(
        mongo_user="user",
        mongo_password="pass@word",
        mongo_host="localhost",
        mongo_port=27017,
        mongo_db_name="testdb"
    )
    # pass@word should be URL encoded as pass%40word
    expected = "mongodb://user:pass%40word@localhost:27017/?authSource=testdb"
    assert settings.mongo_uri == expected

def test_get_settings():
    with patch.dict('os.environ', {
        'MONGO_USER': 'testuser',
        'MONGO_PASSWORD': 'testpassword',
        'MONGO_HOST': 'testcore',
        'MONGO_PORT': '27017',
        'MONGO_DB_NAME': 'testdb'
    }):
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.mongo_user == 'testuser'
        assert isinstance(settings, Settings)
