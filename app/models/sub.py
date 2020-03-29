
from app import db
from app.models.base import Base


class Sub(Base):
    """
    Association table for users subscribing to chats
    """
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), primary_key=True)
