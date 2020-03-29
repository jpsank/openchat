
from app import db
from app.models.base import Base


class Image(Base):
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)

    filename = db.Column(db.String)
    url = db.Column(db.String)

