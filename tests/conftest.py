import pytest
import sqlite3

# Expects: database.init_db(conn) sets up schema in the given connection
from database import init_db

# Expects: app.py exports a Flask instance named `app`
from app import app as flask_app


@pytest.fixture
def db():
    """In-memory SQLite DB, schema applied, torn down after each test."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(db):
    """Flask test client wired to the in-memory test DB."""
    flask_app.config['TESTING'] = True
    flask_app.config['DB'] = db
    with flask_app.test_client() as c:
        yield c
