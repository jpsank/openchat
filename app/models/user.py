from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app, escape
from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from app import db, login
from app.util.helpers import nl2br
from .base import Base
from .vote import Vote
from .sub import Sub
from .post import Post
from .comment import Comment


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, Base):

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # User email information
    email = db.Column(db.String(300), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    about_me = db.Column(db.String(300))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    votes = db.relationship('Vote', backref='user', lazy='dynamic')
    chats = db.relationship('Chat', backref='creator', lazy='dynamic')

    subscriptions = db.relationship(
        'Chat', secondary='sub',
        backref=db.backref('subscribers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    @hybrid_property
    def score(self):
        return sum(p.score for p in self.posts)

    @score.expression
    def score(cls):
        return select([func.sum(Post.score.as_scalar())]).where(Post.author_id == cls.id)

    @property
    def about_me_(self):
        return nl2br(str(escape(self.about_me)))

    # Voting

    def upvote(self, item):
        return self.vote(item, True)

    def downvote(self, item):
        return self.vote(item, False)

    def vote(self, item, liked):
        existing = self.already_voted(item)
        if existing is not None:
            existing.liked = liked
            return existing
        else:
            if isinstance(item, Post):
                return Vote(user_id=self.id, post_id=item.id, liked=liked)
            elif isinstance(item, Comment):
                return Vote(user_id=self.id, comment_id=item.id, liked=liked)

    def withdraw_vote(self, item):
        existing = self.already_voted(item)
        if existing is not None:
            db.session.delete(existing)

    def already_voted(self, item):
        if isinstance(item, Post):
            return self.votes.filter(Vote.post_id == item.id).first()
        elif isinstance(item, Comment):
            return self.votes.filter(Vote.comment_id == item.id).first()

    # Subscriptions

    def set_subscribed(self, chat, sub):
        if sub is True:
            self.subscribe(chat)
        elif sub is False:
            self.unsubscribe(chat)

    def subscribe(self, chat):
        if not self.is_subscribed(chat):
            self.subscriptions.append(chat)

    def unsubscribe(self, chat):
        if self.is_subscribed(chat):
            self.subscriptions.remove(chat)

    def is_subscribed(self, chat):
        return self.subscriptions.filter(
            Sub.chat_id == chat.id).scalar() is not None

    def subscribed_posts(self):
        return Post.query.join(Sub, (Sub.chat_id == Post.chat_id))\
            .filter(Sub.user_id == self.id)

    # Authentication

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    # Custom queries

    @staticmethod
    def get_by_username(username):
        return User.query.filter(func.lower(User.username) == func.lower(username)).first()

    @staticmethod
    def get_by_email(email):
        return User.query.filter(func.lower(User.email) == func.lower(email)).first()
