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
    group_id = db.Column(db.Integer, db.ForeignKey("study_groups.group_id"), nullable = True)
    note_name = db.Column(db.String(80),nullable=False)
    file_path = db.Column(db.String(500),nullable=False)
    time_uploaded = db.Column(db.DateTime(timezone=True),nullable=False,default=datetime.utcnow)

    #create note object
    def create_Note(id,name,path,group_id=None):
        note = Notes(user_id=id,note_name=name,file_path=path,group_id=group_id)
        db.session.add(note)
        db.session.commit()
    
    def get_Note(user_id):
        return Notes.query.filter_by(user_id=user_id).first()




#Summary_notes Schema
class Notes_Summary(db.Model):
    __tablename__ = "notes_summaries"
    summary_id = db.Column(db.Integer,primary_key=True)
    from_notes_id = db.Column(db.Integer,db.ForeignKey("notes.notes_id"),nullable=False)  #matches note_id summary came from
    from_user_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    note_name = db.Column(db.String(80),nullable=False)
    summary_text = db.Column(db.Text,nullable=False)
    time_summarized = db.Column(db.DateTime(timezone=True),nullable=False,default=datetime.utcnow)


    def get_summary(note_id):
        #queries summary for a given note
        return Notes_Summary.query.filter_by(from_notes_id=note_id).first()
    

    def add_summary(from_note_id,user_id,text):
        #Creates summary object if doesnt exist already, otherwise returns generated summary for corresponding note
        curr_summary = Notes_Summary.get_summary(from_note_id)

        if curr_summary:
            return curr_summary

        note = Notes.query.get(from_note_id)
        new_summary = Notes_Summary(from_notes_id=from_note_id,from_user_id=user_id,note_name=note.note_name,summary_text=text)
        db.session.add(new_summary)
        db.session.commit()
        return new_summary
    


    def get_unsummarized_notes(user_id):
        #returns user's notes that dont have a summary with outer join
        #this way when user summarizes no duplicates occur
        return Notes.query.outerjoin(Notes_Summary,Notes.notes_id==Notes_Summary.from_notes_id
                                     ).filter(Notes.user_id==user_id
                                    ).filter(Notes_Summary.summary_id==None).limit(20).all()    #set limit 20 to prevent looking at all notes
        
    


#StudyGroup Scehema(not being used anymore)
class StudyGroup(db.Model):
    __tablename__ = "study_groups"
    group_id = db.Column(db.Integer,primary_key=True)
    group_name = db.Column(db.String(255),nullable=False)
    created_by = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    time_created =  db.Column(db.DateTime(timezone=True), nullable = False, default = datetime.utcnow)
    is_private = db.Column(db.Boolean, nullable=False, default=False)
    invite_code = db.Column(db.String(20), unique=True,  nullable=True)

    def create_group(group_name,created_by_id):
        #create study group object and store in the database
        study_group = StudyGroup(group_name=group_name,created_by=created_by_id)
        db.session.add(study_group)
        db.session.commit()
    


class StudyGroupMember(db.Model):
    __tablename__ = "study_group_members"
    id = db.Column(db.Integer,primary_key=True)
    group_id = db.Column(db.Integer,db.ForeignKey("study_groups.group_id"),nullable=False)
    group_member_id = db.Column(db.Integer,db.ForeignKey("users.user_id"),nullable=False)
    joined_at =  db.Column(db.DateTime(timezone=True), nullable = False, default = datetime.utcnow)
    


#GroupMembership Scehema
class GroupMembership(db.Model):
    __tablename__ = "group_memberships"
    membership_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_groups.group_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    time_joined = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class DocumentAnalysis(db.Model):
    __tablename__ = "document_analysis"
    analysis_id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey("notes.notes_id"), nullable=False, unique=True)
    subject = db.Column(db.JSON, nullable=False)
    topics = db.Column(db.JSON, nullable=False)
    keywords = db.Column(db.JSON, nullable=False)
    academic_level = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.Text, nullable=False)

def create_Doc_Analysis(note_id, metadata):
    return DocumentAnalysis(note_id=note_id, subject=metadata['subject'],
                            topics=metadata['topics'], keywords=metadata['keywords'],
                            academic_level=metadata['academic_level'], summary=metadata['summary'])


# Message Schema
class Message(db.Model):
    __tablename__ = "messages"
    message_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("study_groups.group_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    time_sent = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Automatically joins the user row to easily pull user attributes (like .user.username)
    user = db.relationship("User", backref=db.backref("messages", lazy=True))

    # Create message and store in the database
    @classmethod
    def create_message(cls, group_id, user_id, text):
        msg = cls(group_id=group_id, user_id=user_id, text=text)
        db.session.add(msg)
        db.session.commit()
        return msg

    # Returns most recent messages for a pool, oldest first to display
    @classmethod
    def get_pool_messages(cls, group_id, limit=50):
        rows = cls.query.filter_by(group_id=group_id).order_by(cls.time_sent.desc()).limit(limit).all()
        return list(reversed(rows))
