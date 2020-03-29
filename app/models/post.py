from flask import escape
from sqlalchemy import func, case, select
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from app.models.base import Base
from app.util.helpers import nl2br

from .vote import Vote


class Post(Base):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    body = db.Column(db.String(4000))

    attachment = db.relationship('Image', uselist=False, backref='post')

    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    votes = db.relationship('Vote', backref='post', lazy='dynamic')

    comments = db.relationship('Comment', backref='post')

    def __repr__(self):
        return '<Post {}>'.format(self.title)

    @hybrid_property
    def score(self):
        return sum(1 if v.liked else -1 for v in self.votes)

    @score.expression
    def score(cls):
        v = case([(Vote.liked, 1)], else_=-1)
        return select([func.sum(v)]).where(Vote.post_id == cls.id)

    # def score(self):
    #     return self.votes.filter_by(liked=True).count() - self.votes.filter_by(liked=False).count()

    @property
    def body_e(self):
        return nl2br(str(escape(self.body)))
