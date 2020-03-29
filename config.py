import os
basedir = os.path.abspath(os.path.dirname(__file__))


# CONFIGURATION

DEBUG = True

# Mail
MAIL_SERVER = os.environ.get('MAIL_SERVER')
MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
ADMINS = ['julian@sankergroup.org']

# Pagination
DEFAULT_PER_PAGE = 50
POSTS_PER_PAGE = 50
COMMENTS_PER_PAGE = 50
CHATS_PER_PAGE = 50
USERS_PER_PAGE = 50


# EXTENSIONS

# Flask-SQLAlchemy
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Session
SESSION_TYPE = 'sqlalchemy'

# Flask-Uploads
UPLOADS_DEFAULT_DEST = os.path.join(basedir, 'app/static/uploads/')
UPLOADS_DEFAULT_URL = 'http://localhost:5000/static/uploads/'
UPLOADED_IMAGES_DEST = os.path.join(basedir, 'app/static/uploads/')
UPLOADED_IMAGES_URL = 'http://localhost:5000/static/uploads/'