import pytest
from database.database import db
from database.models import User,Notes,Notes_Summary



#Circle back to this later to fix issue with testing database functions.
# class TestAddSummary:
#     def test_add_summary_regular(self,db):
#         #add summary on none-existing summary
#         user = User(username="cailan",email="cailan@gmail.com", password="secret")
#         db.session.add(user)
#         db.session.commit()

#         note = Notes(user_id = user.user_id,note_name="calculus.pdf",file_path="/school/calculus.pdf")
#         db.session.add(note)
#         db.session.commit()
        
#         summary = Notes_Summary.add_summary(note.notes_id,user.user_id,"Testing some text for coding project")
        
#         assert summary is not None, "Summary returned should not be empty"
#         assert summary.from_notes_id == note.notes_id, "Note_id should match"
#         assert summary.from_user_id == user.user_id, "user_ids should match"
#         assert summary.summary_text == "Testing some text for coding project", "Text generated should match"
    

  
    


        


        






##NOT IMPLEMENTED AS FUNCTIONS IMBEDDED IN REGISTER ROUTE
# class TestCreateUser:
#     def test_returns_user_id(self, db):
#         # create a user with (username, email, password) and assert the returned value is a positive integer user_id
#         pass

#     def test_duplicate_email_raises(self, db):
#         # create two users with the same email and assert an exception is raised
#         pass

#     def test_duplicate_username_raises(self, db):
#         # create two users with the same username and assert an exception is raised
#         pass


# class TestGetUserByEmail:
#     def test_returns_user(self, db):
#         # create a user, look them up by email, assert user.username matches
#         pass

#     def test_missing_email_returns_none(self, db):
#         # look up an email that was never inserted and assert None is returned
#         pass


class TestNotes:
    def test_create_note_returns_notes_id(self, db):
        # create a user, create a note linked to that user_id with (note_name, file_path)
        # assert the returned value is a positive integer notes_id
        pass

    def test_get_notes_by_user_returns_list(self, db):
        # create a user, upload two notes for that user
        # assert get_notes_by_user returns a list with both notes
        pass

    def test_get_notes_invalid_user_returns_empty(self, db):
        # call get_notes_by_user with a nonexistent user_id and assert an empty list is returned
        pass


class TestNotesSummary:
    def test_create_summary_returns_summary_id(self, db):
        # create a user and a note, then create a summary linked to both
        # assert the returned value is a positive integer summary_id
        pass

    def test_summary_text_saved_correctly(self, db):
        # create a summary and fetch it back, assert summary_text matches what was saved
        pass


class TestCreateStudyGroup:
    def test_returns_group_id(self, db):
        # create a user, create a group with (group_name, created_by=user_id)
        # assert the returned value is a positive integer group_id
        pass

    def test_invalid_created_by_raises(self, db):
        # pass a nonexistent user_id as created_by and assert an exception is raised
        pass


class TestGroupMembers:
    def test_add_and_retrieve_member(self, db):
        # create a user and a group, add the user as a member
        # assert they appear in get_group_members
        pass

    def test_duplicate_member_raises(self, db):
        # add the same user to a group twice and assert an exception is raised
        pass

    def test_empty_group_returns_empty_list(self, db):
        # create a group with no members and assert get_group_members returns []
        pass
