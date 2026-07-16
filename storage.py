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
    content_type = file_storage.content_type
    note_id = str(uuid.uuid4())
    storage_path = f"{note_id}.{extension}"
    get_supabase().storage.from_(BUCKET_NAME).upload(storage_path, file_storage.read(), file_options={"content-type": content_type})
    return note_id,storage_path

# Retrieves the signed URL for a note file so that it can be accessed by users.
def get_note_file(file_path):
    expires_in_seconds = 3600  # 1 hour
    data = get_supabase().storage.from_(BUCKET_NAME).create_signed_url(file_path, expires_in_seconds)  # retrieves a dictionary of the signed URL
    return data['signedUrl']  # returns the actual url to the actual file bytes 


def delete_note_file(file_path):
    return get_supabase().storage.from_(BUCKET_NAME).remove([file_path])