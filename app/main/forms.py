from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, SelectField
from flask_wtf.file import FileAllowed
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import User, Chat
from app import db, images


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me',
                             validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class PostForm(FlaskForm):
    chat_name = SelectField('Chat')
    title = StringField('Title', validators=[DataRequired()])
    body = TextAreaField('Say something')
    image = FileField('Image', validators=[FileAllowed(images, 'Image Only!')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.chat_name.choices = [(c[0], c[0]) for c in db.session.query(Chat.name).all()]


class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ChatForm(FlaskForm):
    name = StringField('Create a new chat', validators=[DataRequired()])
    about = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditChatForm(FlaskForm):
    about = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    search = StringField('Search')

