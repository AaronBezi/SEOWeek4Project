import os
import uuid
from supabase import create_client

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}
BUCKET_NAME = os.getenv('SUPABASE_NOTES_BUCKET', 'notes')

_supabase = None


def get_supabase():
    global _supabase
    if _supabase is None:
        _supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    return _supabase


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_note_file(file_storage):
    extension = file_storage.filename.rsplit('.', 1)[1].lower()
    note_id = str(uuid.uuid4())
    storage_path = f"{note_id}.{extension}"
    get_supabase().storage.from_(BUCKET_NAME).upload(storage_path, file_storage.read())
    return note_id
