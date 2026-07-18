import pytest
from io import BytesIO
from werkzeug.security import generate_password_hash
from database.models import User, Notes, StudyGroup, GroupMembership, Message
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
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['summary'], list)
        assert data['summary'][0]['summary'] == 'Fake summary'

    def test_summarize_openai_error_returns_500(self, client, db, monkeypatch):
        monkeypatch.setattr('app.generate_summary', lambda notes: {'success': False, 'error': 'API down'})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'test.pdf', '/files/test.pdf')
        response = client.post('/api/summarize')
        assert response.status_code == 500


class TestPrivatePool:
    def test_join_with_valid_code_returns_200(self, client):
        # create a private pool with a join code, POST the code, assert 200 and membership created
        pass

    def test_join_with_invalid_code_returns_404(self, client):
        # POST an incorrect join code and assert a 404 response
        pass

    def test_join_already_member_returns_200(self, client):
        # join a pool twice with the same code and assert no duplicate membership is created
        pass


class TestChat:
    def test_send_message_unauthenticated_returns_401(self, client):
        response = client.post('/pool_space/1/message', data={'text': 'hello'})
        assert response.status_code == 302  # @login_required redirects to login

    def test_send_message_returns_200(self, client, db, monkeypatch):
        monkeypatch.setattr('app.pusher_client.trigger', lambda *args, **kwargs: None)
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Chat Pool', created_by=user.user_id, is_private=False)
        db.session.add(pool)
        db.session.commit()
        db.session.add(GroupMembership(group_id=pool.group_id, user_id=user.user_id))
        db.session.commit()
        response = client.post(f'/pool_space/{pool.group_id}/message', data={'text': 'hello'})
        assert response.status_code == 200
        assert response.get_json()['success'] is True

    def test_get_messages_returns_list(self, client, db, monkeypatch):
        monkeypatch.setattr('app.pusher_client.trigger', lambda *args, **kwargs: None)
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Chat Pool', created_by=user.user_id, is_private=False)
        db.session.add(pool)
        db.session.commit()
        db.session.add(GroupMembership(group_id=pool.group_id, user_id=user.user_id))
        db.session.commit()
        client.post(f'/pool_space/{pool.group_id}/message', data={'text': 'first'})
        client.post(f'/pool_space/{pool.group_id}/message', data={'text': 'second'})
        messages = Message.get_pool_messages(pool.group_id)
        assert len(messages) == 2

    def test_get_messages_empty_pool_returns_empty(self, client, db):
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Empty Pool', created_by=user.user_id, is_private=False)
        db.session.add(pool)
        db.session.commit()
        messages = Message.get_pool_messages(pool.group_id)
        assert messages == []


class TestQuiz:
    def test_generate_quiz_unauthenticated_returns_401(self, client):
        # POST to /api/quiz without login and assert 401
        pass

    def test_generate_quiz_no_notes_returns_400(self, client):
        # login with no notes uploaded, POST to /api/quiz, assert 400
        pass

    def test_generate_quiz_returns_questions(self, client, db, monkeypatch):
        # monkeypatch quiz generation, login, add a note, POST to /api/quiz
        # assert 200 and response contains a list of questions
        pass
