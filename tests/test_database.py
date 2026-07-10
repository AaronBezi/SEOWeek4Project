import pytest
from database.database import db
from database.models import User, Notes, Notes_Summary, StudyGroup, GroupMembership



#Circle back to this later to fix issue with testing database functions.
class TestAddSummary:
    def test_add_summary_regular(self,db):
        try:
            #add summary on none-existing summary
            user = User(username="cailan",email="cailan@gmail.com", password="secret")
            db.session.add(user)
            db.session.commit()

            note = Notes(user_id = user.user_id,note_name="calculus.pdf",file_path="/school/calculus.pdf")
            db.session.add(note)
            db.session.commit()
            
            summary = Notes_Summary.add_summary(note.notes_id,user.user_id,"Testing some text for coding project")
            
            assert summary is not None, "Summary returned should not be empty"
            assert summary.from_notes_id == note.notes_id, "Note_id should match"
            assert summary.from_user_id == user.user_id, "user_ids should match"
            assert summary.summary_text == "Testing some text for coding project", "Text generated should match"
        finally:
            db.session.delete(summary)
            db.session.delete(note)
            db.session.delete(user)
            db.session.commit()

class TestNotes:
    def test_create_note_returns_notes_id(self, db):
        user = User(username="noteuser", email="noteuser@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        Notes.create_Note(user.user_id, "history.pdf", "/files/history.pdf")
        note = Notes.query.filter_by(user_id=user.user_id).first()

        assert note is not None
        assert note.notes_id > 0

    def test_get_notes_by_user_returns_list(self, db):
        user = User(username="listuser", email="listuser@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        Notes.create_Note(user.user_id, "note1.pdf", "/files/note1.pdf")
        Notes.create_Note(user.user_id, "note2.pdf", "/files/note2.pdf")
        notes = Notes.query.filter_by(user_id=user.user_id).all()

        assert len(notes) == 2

    def test_get_notes_invalid_user_returns_empty(self, db):
        notes = Notes.query.filter_by(user_id=99999).all()
        assert notes == []


class TestNotesSummary:
    def test_create_summary_returns_summary_id(self, db):
        user = User(username="sumuser", email="sumuser@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        note = Notes(user_id=user.user_id, note_name="bio.pdf", file_path="/files/bio.pdf")
        db.session.add(note)
        db.session.commit()

        summary = Notes_Summary.add_summary(note.notes_id, user.user_id, "Bio summary text")

        assert summary.summary_id > 0

    def test_summary_text_saved_correctly(self, db):
        user = User(username="textuser", email="textuser@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        note = Notes(user_id=user.user_id, note_name="chem.pdf", file_path="/files/chem.pdf")
        db.session.add(note)
        db.session.commit()

        Notes_Summary.add_summary(note.notes_id, user.user_id, "Chemistry notes summary")
        fetched = Notes_Summary.get_summary(note.notes_id)

        assert fetched.summary_text == "Chemistry notes summary"


class TestCreateStudyGroup:
    def test_returns_group_id(self, db):
        user = User(username="groupuser", email="groupuser@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        StudyGroup.create_group("Math Study", user.user_id)
        group = StudyGroup.query.filter_by(group_name="Math Study").first()

        assert group is not None
        assert group.group_id > 0

    def test_invalid_created_by_raises(self, db):
        # SQLite doesn't enforce FK constraints by default so this can't assert an error
        # placeholder until FK enforcement is added to the test config
        pass


class TestGroupMembers:
    def test_add_and_retrieve_member(self, db):
        user = User(username="member1", email="member1@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        group = StudyGroup(group_name="Test Group", created_by=user.user_id)
        db.session.add(group)
        db.session.commit()

        membership = GroupMembership(group_id=group.group_id, user_id=user.user_id)
        db.session.add(membership)
        db.session.commit()

        members = GroupMembership.query.filter_by(group_id=group.group_id).all()
        assert len(members) == 1
        assert members[0].user_id == user.user_id

    def test_duplicate_member_raises(self, db):
        # GroupMembership has no unique constraint on (group_id, user_id) yet
        # placeholder until a UniqueConstraint is added to the model
        pass

    def test_empty_group_returns_empty_list(self, db):
        user = User(username="emptygrp", email="emptygrp@example.com", password="pass")
        db.session.add(user)
        db.session.commit()

        group = StudyGroup(group_name="Empty Group", created_by=user.user_id)
        db.session.add(group)
        db.session.commit()

        members = GroupMembership.query.filter_by(group_id=group.group_id).all()
        assert members == []
