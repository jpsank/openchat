from sqlalchemy import func

from app import db
from app.models.base import Base


class Chat(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    about = db.Column(db.String(4000))

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posts = db.relationship('Post', backref='chat', lazy='dynamic')

    def __repr__(self):
        return '<Chat {}>'.format(self.name)

    # Custom queries

    @staticmethod
    def get_by_name(name):
        return Chat.query.filter(func.lower(Chat.name) == func.lower(name)).first()

