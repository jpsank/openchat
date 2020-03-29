from app import app

from app.blueprints.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app.blueprints.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from app.blueprints.main import bp as main_bp
app.register_blueprint(main_bp)
