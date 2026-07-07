from .database import db
from datetime import datetime
#File used to create Schemas for the database

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(20),nullable=False)
    time_created = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)




    


