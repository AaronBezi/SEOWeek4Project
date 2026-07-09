import pytest
from io import BytesIO
from werkzeug.security import generate_password_hash
from database.models import User
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


class TestGroups:
    # waiting on Diego to add /groups routes
    def test_get_groups_returns_list(self, client):
        # GET /groups and assert the response is a JSON list
        pass

    def test_create_group_returns_201(self, client):
        # POST to /groups with {group_name, created_by (user_id)} and assert 201 with a group_id
        pass

    def test_create_group_missing_fields_returns_400(self, client):
        # POST to /groups without group_name or created_by and assert a 400 response
        pass

    def test_get_group_by_id_returns_group(self, client):
        # create a group then GET /groups/<group_id> and assert group_name matches
        pass

    def test_get_nonexistent_group_returns_404(self, client):
        # GET /groups/9999 for a group that does not exist and assert a 404 response
        pass


class TestSummarizeRoute:
    # waiting on Diego to add /summarize route
    def test_summarize_returns_text(self, client, monkeypatch):
        # monkeypatch summarize_text to return a fake summary
        # POST a note_id to /summarize and assert a non-empty summary string is returned
        pass

    def test_summarize_missing_note_id_returns_400(self, client):
        # POST to /summarize with no note_id and assert a 400 response
        pass
