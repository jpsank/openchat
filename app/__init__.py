import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_uploads import UploadSet, IMAGES, configure_uploads

from config import Config, basedir

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'auth.login'
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from app.main import bp as main_bp
app.register_blueprint(main_bp)

if not app.debug and not app.testing:
    logs_path = os.path.join(basedir, 'logs')
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)
    file_handler = RotatingFileHandler(os.path.join(logs_path, 'openchat.log'),
                                       maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('OpenChat startup')


from app import models
