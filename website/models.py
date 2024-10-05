from . import db, admin
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_admin.contrib.sqla import ModelView



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))


class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now(), nullable=True)
    caption = db.Column(db.String(1000), nullable=True)
    descp = db.Column(db.String(10000), nullable=True)
    file_url = db.Column(db.String(2000), nullable=True)
    locationx = db.Column(db.String(100000000), nullable=True)
    locationy = db.Column(db.String(100000000), nullable=True)
    voice_note = db.Column(db.String(100000000), nullable=True)
   
class MemoryView(ModelView):
    pass

admin.add_view(MemoryView(Memory, db.session))  
