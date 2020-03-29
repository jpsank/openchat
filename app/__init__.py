import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_uploads import UploadSet, IMAGES, configure_uploads

import config

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(config)
app.config.from_pyfile('config.py')

# Initialize Sentry if possible
if app.config['SENTRY_DSN']:
    sentry_sdk.init(
        dsn=app.config['SENTRY_DSN'],
        integrations=[FlaskIntegration(), SqlalchemyIntegration()]
    )

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'auth.login'
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

# Blueprints
from app import blueprints

from app.util import filters
from app import models
