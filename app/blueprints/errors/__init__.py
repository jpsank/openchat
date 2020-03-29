from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.blueprints.errors import handlers
