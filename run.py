from app import app, db, cli
from app.models import User

cli.register(app.cli)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}


if __name__ == '__main__':
    app.run()
