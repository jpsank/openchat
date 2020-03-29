from sqlalchemy import func, case, select
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from app.models.base import Base

from .vote import Vote


class Comment(Base):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(4000))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    votes = db.relationship('Vote', backref='comment', lazy='dynamic')

    comments = db.relationship('Comment', lazy='dynamic')

    @hybrid_property
    def score(self):
        return sum(1 if v.liked else -1 for v in self.votes)

    @score.expression
    def score(cls):
        v = case([(Vote.liked, 1)], else_=-1)
        return select([func.sum(v)]).where(Vote.post_id == cls.id)
