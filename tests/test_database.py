import pytest
from database.models import Notes,User
from database.database import db


class TestCreateUser:
    def test_returns_user_id(self, db):
        # create a user with (username, email, password) and assert the returned value is a positive integer id
        pass

    def test_duplicate_email_raises(self, db):
        # create two users with the same email and assert an exception is raised
        pass

    def test_duplicate_username_raises(self, db):
        # create two users with the same username and assert an exception is raised
        pass


class TestGetUserByEmail:
    def test_returns_user(self, db):
        # create a user, look them up by email, assert user.username matches
        pass

    def test_missing_email_returns_none(self, db):
        # look up an email that was never inserted and assert None is returned
        pass


class TestCreateStudyGroup:
    # waiting on StudyGroup model to be added to models.py
    def test_returns_group_id(self, db):
        # create a user, create a group owned by them, assert a positive integer id is returned
        pass

    def test_invalid_owner_raises(self, db):
        # pass a nonexistent owner id and assert an exception is raised
        pass


class TestGroupMembers:
    # waiting on StudyGroup model to be added to models.py
    def test_add_and_retrieve_member(self, db):
        # add a member to a group and assert they appear in get_group_members
        pass

    def test_duplicate_member_raises(self, db):
        # add the same user to a group twice and assert an exception is raised
        pass

    def test_empty_group_returns_empty_list(self, db):
        # create a group with no members and assert get_group_members returns []
        pass

class TestCreateNote:
    def test_create_note(self,db):
        user = User(username="Testing123",email="testing245@gmail.com",password="sceret")
        db.session.add(user)
        db.session.commit()
        note_id = Notes.create_Note(user.user_id,"lecture.pdf","/tmp/lecture.pdf")
        note = Notes.query.filter_by(notes_id=note_id).first()
        
        assert note is not None
        assert note.user_id == user.user_id
        assert note.note_name == "lecture.pdf"
        assert note.file_path == "/tmp/lecture.pdf"
        


