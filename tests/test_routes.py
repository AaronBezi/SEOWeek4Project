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
        response = client.post('/api/summarize', json={})
        assert response.status_code == 400

    def test_summarize_returns_200_with_summary(self, client, db, monkeypatch):
        monkeypatch.setattr('app.generate_summary', lambda notes: {'success': True, 'summary': 'Fake summary'})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'test.pdf', '/files/test.pdf')
        response = client.post('/api/summarize', json={})
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
        response = client.post('/api/summarize', json={})
        assert response.status_code == 500


class TestPrivatePool:
    def test_join_with_valid_code_creates_membership(self, client, db):
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Private Pool', created_by=user.user_id,
                          is_private=True, invite_code='SECRET99')
        db.session.add(pool)
        db.session.commit()

        client.post(f'/join_pool/{pool.group_id}/join',
                    data={'code': 'SECRET99'}, follow_redirects=False)

        membership = GroupMembership.query.filter_by(
            group_id=pool.group_id, user_id=user.user_id
        ).first()
        assert membership is not None

    def test_join_with_invalid_code_rejected(self, client, db):
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Private Pool', created_by=user.user_id,
                          is_private=True, invite_code='SECRET99')
        db.session.add(pool)
        db.session.commit()

        res = client.post(f'/join_pool/{pool.group_id}/join',
                          data={'code': 'WRONGCODE'}, follow_redirects=False)

        membership = GroupMembership.query.filter_by(
            group_id=pool.group_id, user_id=user.user_id
        ).first()
        assert membership is None
        assert res.status_code == 302
        assert '/join_pool' in res.headers['Location']

    def test_join_already_member_does_not_duplicate(self, client, db):
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        pool = StudyGroup(group_name='Public Pool', created_by=user.user_id, is_private=False)
        db.session.add(pool)
        db.session.commit()
        db.session.add(GroupMembership(group_id=pool.group_id, user_id=user.user_id))
        db.session.commit()

        client.post(f'/join_pool/{pool.group_id}/join', data={})

        memberships = GroupMembership.query.filter_by(
            group_id=pool.group_id, user_id=user.user_id
        ).all()
        assert len(memberships) == 1


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
        response = client.post('/api/generate_quiz', json={})
        assert response.status_code == 401

    def test_generate_quiz_no_notes_returns_400(self, client):
        register_user(client)
        login_user_via_form(client)
        response = client.post('/api/generate_quiz', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'No notes found' in data['error']

    def test_generate_quiz_returns_questions(self, client, db, monkeypatch):
        monkeypatch.setattr('app.generate_summary', lambda note: {'success': True, 'summary': 'Fake summary text'})
        monkeypatch.setattr('app.generate_quiz_from_summary', lambda text: {
            'success': True,
            'quiz_data': {'quiz': [{'question': 'What is X?', 'answer': 'X is Y.'}]}
        })
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'test.pdf', '/files/test.pdf')
        response = client.post('/api/generate_quiz', json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['quiz'], list)
        assert data['quiz'][0]['question'] == 'What is X?'


class TestRecommendations:
    def test_recommendations_unauthenticated_returns_401(self, client):
        response = client.post('/api/recommendations', json={})
        assert response.status_code == 401

    def test_recommendations_no_notes_returns_400(self, client):
        register_user(client)
        login_user_via_form(client)
        response = client.post('/api/recommendations', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data

    def test_recommendations_returns_books(self, client, db, monkeypatch):
        mock_books = [{'title': 'Biology 101', 'authors': ['Dr. Smith'], 'description': 'A textbook.'}]
        monkeypatch.setattr('app.search_books', lambda query: {'success': True, 'books': mock_books})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'biology.pdf', '/files/biology.pdf')
        response = client.post('/api/recommendations', json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['recommendations'] == mock_books

    def test_recommendations_books_api_failure_returns_400(self, client, db, monkeypatch):
        monkeypatch.setattr('app.search_books', lambda query: {'success': False, 'error': 'API unavailable'})
        register_user(client)
        login_user_via_form(client)
        user = db.session.query(User).filter_by(email='test@example.com').first()
        Notes.create_Note(user.user_id, 'biology.pdf', '/files/biology.pdf')
        response = client.post('/api/recommendations', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
