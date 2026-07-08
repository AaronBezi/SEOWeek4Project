from .database import db
from datetime import datetime
from sqlalchemy import func
from flask_login import LoginManager, current_user, UserMixin, login_user
#File used to create Schemas for the database

#User table schema
class User(UserMixin,db.Model):
    __tablename__ = "users"     #easier access for database
    user_id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128),nullable=False)
    time_created = db.Column(db.DateTime(timezone=True), nullable = False, default = datetime.utcnow)


    def get_id(self):
        return str(self.user_id)        #tells flask_login how to get user_id



#Notes schema
class Notes(db.Model):
    __tablename__ = "notes"
    notes_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),nullable = False)  #matches user_id of user who uploaded the note
    note_name = db.Column(db.String(80),nullable=False)
    file_path = db.Column(db.String(500),nullable=False)
    time_uploaded = db.Column(db.DateTime(timezone=True),nullable=False,default=datetime.utcnow)

    #create note object
    def create_Note(id,name,path):
        note = Notes(user_id=id,note_name=name,file_path=path)
        db.session.add(note)
        db.session.commit()



#Summary_notes Schema
class Notes_Summary(db.Model):
    __tablename__ = "notes_summaries"
    summary_id = db.Column(db.Integer,primary_key=True)
    from_notes_id = db.Column(db.Integer,db.ForeignKey("notes.notes_id"),nullable=False)  #matches note_id summary came from
    from_user_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    note_name = db.Column(db.String(80),nullable=False)
    summary_text = db.Column(db.Text,nullable=False)
    time_summarized = db.Column(db.DateTime(timezone=True),nullable=False,default=datetime.utcnow)

    def add_summary(from_notes_id,from_user_id,note_name,summary_text):
        pass



#StudyGroup Scehema
class StudyGroup(db.Model):
    __tablename__ = "study_groups"
    group_id = db.Column(db.Integer,primary_key=True)
    group_name = db.Column(db.String(255),nullable=False)
    created_by = db.Column(db.Integer,db.ForeginKey("users.user_id"),nullable=False)
    time_created =  db.Column(db.DateTime(timezone=True), nullable = False, default = datetime.utcnow)


