from flask import render_template
from app import db
from app.blueprints.errors import bp
from werkzeug.exceptions import RequestEntityTooLarge


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


@bp.errorhandler(413)
@bp.errorhandler(RequestEntityTooLarge)
def file_too_large_error(error):
    return render_template('errors/413.html'), 413