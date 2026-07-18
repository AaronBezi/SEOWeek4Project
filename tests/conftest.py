import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ.setdefault('PUSHER_APP_ID', '123456')
os.environ.setdefault('PUSHER_KEY', 'test')
os.environ.setdefault('PUSHER_SECRET', 'test')
os.environ.setdefault('PUSHER_CLUSTER', 'test')

import pytest
from sqlalchemy.pool import StaticPool
from app import app as flask_app
from database.database import db as _db


@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        },
    })

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db
