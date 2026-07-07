import pytest
from io import BytesIO


class TestUploadNotes:
    def test_upload_valid_file_returns_200(self, client, monkeypatch):
        monkeypatch.setattr('app.upload_note_file', lambda file: 'fake-note-id')
        data = {'file': (BytesIO(b'hello world'), 'notes.pdf')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert response.get_json()['note_id'] == 'fake-note-id'

    def test_upload_missing_file_returns_400(self, client):
        response = client.post('/upload', data={}, content_type='multipart/form-data')
        assert response.status_code == 400

    def test_upload_unsupported_format_returns_400(self, client):
        data = {'file': (BytesIO(b'hello'), 'notes.exe')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 400


class TestGroups:
    def test_get_groups_returns_list(self, client):
        # GET /groups and assert the response is a JSON list
        pass

    def test_create_group_returns_201(self, client):
        # POST to /groups with a valid owner_id and assert a 201 response with a group ID
        pass

    def test_create_group_missing_owner_returns_400(self, client):
        # POST to /groups without owner_id and assert a 400 response
        pass

    def test_get_group_by_id_returns_group(self, client):
        # create a group then GET /groups/<id> and assert the correct group is returned
        pass

    def test_get_nonexistent_group_returns_404(self, client):
        # GET /groups/9999 for a group that does not exist and assert a 404 response
        pass


class TestSummarizeRoute:
    def test_summarize_returns_text(self, client):
        # POST text to /summarize and assert a non-empty summary string is returned
        pass

    def test_summarize_missing_text_returns_400(self, client):
        # POST to /summarize with no text body and assert a 400 response
        pass
