import pytest
from io import BytesIO
from werkzeug.security import generate_password_hash
from database.models import User, Notes
from database.database import db as _db


def register_user(client, username='testuser', email='test@example.com',
                  password='password123'):
    return client.post('/register', data={
        'username': username,
        'email': email,
        'password': password,
        'confirm_password': password,
    }, follow_redirects=True)


def login_user_via_form(client, email='test@example.com', password='password123'):
    return client.post('/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)


class TestRegister:
    def test_get_register_returns_200(self, client):
        response = client.get('/register')
        assert response.status_code == 200

    def test_valid_registration_redirects(self, client):
        response = register_user(client)
        assert response.status_code == 200
        assert b'Account created' in response.data

    def test_duplicate_username_stays_on_form(self, client):
        register_user(client, username='testuser', email='first@example.com')
        response = register_user(client, username='testuser', email='second@example.com')
        assert b'Register' in response.data

    def test_duplicate_email_stays_on_form(self, client):
        register_user(client, username='user1', email='same@example.com')
        response = register_user(client, username='user2', email='same@example.com')
        assert b'Register' in response.data

    def test_mismatched_passwords_stays_on_form(self, client):
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different456',
        }, follow_redirects=True)
        assert b'Register' in response.data


class TestLogin:
    def test_get_login_returns_200(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    def test_valid_login_redirects(self, client):
        register_user(client)
        response = login_user_via_form(client)
        assert response.status_code == 200
        assert b'Welcome back' in response.data

    def test_wrong_password_stays_on_form(self, client):
        register_user(client)
        response = login_user_via_form(client, password='wrongpassword')
        assert b'Invalid email or password' in response.data

    def test_nonexistent_email_stays_on_form(self, client):
        response = login_user_via_form(client, email='nobody@example.com')
        assert b'Invalid email or password' in response.data


class TestUploadNotes:
    def test_upload_unauthenticated_returns_401(self, client):
        data = {'file': (BytesIO(b'hello world'), 'notes.pdf')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 401

    def test_upload_valid_file_returns_200(self, client, monkeypatch):
        monkeypatch.setattr('app.upload_note_file', lambda file: ('fake-storage-id', 'fake/path.pdf'))
        monkeypatch.setattr('app.Notes.create_Note', lambda id, name, path, group_id=None: None)
        register_user(client)
        login_user_via_form(client)
        data = {'file': (BytesIO(b'hello world'), 'notes.pdf')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert response.get_json()['storage_note_id'] == 'fake-storage-id'

    def test_upload_missing_file_returns_400(self, client):
        register_user(client)
        login_user_via_form(client)
        response = client.post('/upload', data={}, content_type='multipart/form-data')
        assert response.status_code == 400

    def test_upload_unsupported_format_returns_400(self, client):
        register_user(client)
        login_user_via_form(client)
        data = {'file': (BytesIO(b'hello'), 'notes.exe')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400

class TestSummarizeRoute:
    def test_summarize_unauthenticated_returns_401(self, client):
        response = client.post('/api/summarize')
        assert response.status_code == 401

    def test_summarize_no_notes_returns_400(self, client):
        register_user(client)
        login_user_via_form(client)
        response = client.post('/api/summarize')
        assert response.status_code == 400

    def test_summarize_returns_200_with_summary(self, client, db, monkeypatch):
        monkeypatch.setattr('app.generate_summary', lambda notes: {'success': True, 'summary': 'Fake summary'})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'test.pdf', '/files/test.pdf')
        response = client.post('/api/summarize')
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        assert response.get_json()['summary'] == 'Fake summary'

    def test_summarize_openai_error_returns_500(self, client, db, monkeypatch):
        monkeypatch.setattr('app.generate_summary', lambda notes: {'success': False, 'error': 'API down'})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'test.pdf', '/files/test.pdf')
        response = client.post('/api/summarize')
        assert response.status_code == 500
