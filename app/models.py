from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app, url_for, escape
from flask_login import UserMixin, current_user
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os

from app.util.filters import nl2br
from app import db, login, basedir, Config


class Base(db.Model):
    __abstract__ = True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Followers

class Follow(Base):
    """
    Association table for users following chats
    """
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), primary_key=True)


# Likes

class Vote(Base):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    liked = db.Column(db.Boolean)


# Users

class User(UserMixin, Base):

    id = db.Column(db.Integer, primary_key=True)

    # User authentication information
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    chats = db.relationship('Chat', backref='creator', lazy='dynamic')

    votes = db.relationship('Vote', backref='user', lazy='dynamic')

    follows = db.relationship(
        'Chat', secondary='follow',
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {} {}>'.format(self.username, self.email)

    @property
    def about_me_e(self):
        return nl2br(str(escape(self.about_me)))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def score(self):
        score = 0
        for post in self.posts:
            score += post.score()
        return score

    # Voting on posts

    def upvote(self, post):
        vote = self.already_voted(post)
        if vote is not None:
            vote.liked = True
            return vote
        else:
            return Vote(user_id=self.id, post_id=post.id, liked=True)

    def downvote(self, post):
        vote = self.already_voted(post)
        if vote is not None:
            vote.liked = False
            return vote
        else:
            return Vote(user_id=self.id, post_id=post.id, liked=False)

    def already_voted(self, post):
        return self.votes.filter(Vote.post_id == post.id).first()

    # Following chats

    def follow(self, chat):
        if not self.is_following(chat):
            self.follows.append(chat)

    def unfollow(self, chat):
        if self.is_following(chat):
            self.follows.remove(chat)

    def is_following(self, chat):
        return self.follows.filter(
            Follow.chat_id == chat.id).scalar() is not None

    def followed_posts(self):
        followed = Post.query.join(Follow, (Follow.chat_id == Post.chat_id))\
            .filter(Follow.user_id == self.id)
        return followed.order_by(Post.created_at.desc())

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

    @staticmethod
    def get_by_username(username):
        return User.query.filter(func.lower(User.username) == func.lower(username)).first()

    @staticmethod
    def get_by_email(email):
        return User.query.filter(func.lower(User.email) == func.lower(email)).first()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# Posts

class Post(Base):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.String(2048))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))

    comments = db.relationship('Comment', backref='post')

    votes = db.relationship('Vote', backref='post', lazy='dynamic')

    attachment = db.relationship('Image', uselist=False, backref='post')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def score(self):
        return self.votes.filter_by(liked=True).count() - self.votes.filter_by(liked=False).count()

    @property
    def body_e(self):
        return nl2br(str(escape(self.body)))


class Comment(Base):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(512))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

    comments = db.relationship('Comment', lazy='dynamic')


class Chat(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    about = db.Column(db.String(512))

    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    posts = db.relationship('Post', backref='chat', lazy='dynamic')

    def __repr__(self):
        return '<Chat {}>'.format(self.name)

    @staticmethod
    def get_by_name(name):
        return Chat.query.filter(func.lower(Chat.name) == func.lower(name)).first()


# Images

class Image(Base):
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)

    filename = db.Column(db.String(300))
    url = db.Column(db.String(300))

