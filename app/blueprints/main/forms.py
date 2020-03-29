from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

from app import db, images
from app.models import Chat, User, Post, Comment
from app.util.validators import ValidName, Unique, ValidLength


class NewPostForm(FlaskForm):
    chat_name = SelectField('Chat', validators=[DataRequired('Please select a chat')])
    title = StringField('Title', validators=[DataRequired(), ValidLength(Post.title)])
    body = TextAreaField('Text area', validators=[ValidLength(Post.body)])
    image = FileField('Image', validators=[FileAllowed(images, 'Image Only!')])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_name.choices = [(0, '-----')] + [(chat.name, chat.name) for chat in Chat.query.all()]


class NewChatForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), ValidLength(Chat.name), ValidName(),
                                           Unique(Chat.get_by_name, 'That chat name is already taken.')])
    about = TextAreaField('Description', validators=[DataRequired(), ValidLength(Chat.about)])
    submit = SubmitField('Submit')


class NewCommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired(), ValidLength(Comment.body)])
    submit = SubmitField('Submit')


class SearchForm(FlaskForm):
    search = StringField('Search')


class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me',
                             validators=[ValidLength(User.about_me)])
    submit = SubmitField('Submit')


class EditChatForm(FlaskForm):
    about = TextAreaField('Description', validators=[ValidLength(Chat.about)])
    submit = SubmitField('Submit')
