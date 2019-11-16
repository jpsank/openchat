import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # MAIL_SERVER = "smtp.googlemail.com"
    # MAIL_PORT = 587
    # MAIL_USE_TLS = 1
    # MAIL_USERNAME = ""
    # MAIL_PASSWORD = ""
    ADMINS = ['julian@sankergroup.org']

    POSTS_PER_PAGE = 25
    COMMENTS_PER_PAGE = 50
    CHATS_PER_PAGE = 25

    UPLOADS_DEFAULT_DEST = basedir + '/app/static/img/'
    UPLOADS_DEFAULT_URL = 'http://localhost:5000/static/img/'

    UPLOADED_IMAGES_DEST = basedir + '/app/static/img/'
    UPLOADED_IMAGES_URL = 'http://localhost:5000/static/img/'

