import pytest
from database import (
    create_user,
    get_user_by_email,
    create_study_group,
    add_member_to_group,
    get_group_members,
)


class TestCreateUser:
    def test_returns_user_id(self, db):
        # create a user and assert the returned value is a positive integer ID
        pass

    def test_duplicate_email_raises(self, db):
        # create two users with the same email and assert an exception is raised
        pass


class TestGetUserByEmail:
    def test_returns_user_dict(self, db):
        # create a user, look them up by email, assert their fields match
        pass

    def test_missing_email_returns_none(self, db):
        # look up an email that was never inserted and assert None is returned
        pass


class TestCreateStudyGroup:
    def test_returns_group_id(self, db):
        # create a user, create a group owned by them, assert a positive integer ID is returned
        pass

    def test_invalid_owner_raises(self, db):
        # pass a nonexistent owner_id and assert an exception is raised
        pass


class TestGroupMembers:
    def test_add_and_retrieve_member(self, db):
        # add a member to a group and assert they appear in get_group_members
        pass

    def test_duplicate_member_raises(self, db):
        # add the same user to a group twice and assert an exception is raised
        pass

    def test_empty_group_returns_empty_list(self, db):
        # create a group with no members and assert get_group_members returns []
        pass
