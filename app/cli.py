import os
import click
from app import db


def register(app):
    @app.cli.command()
    def init():
        print("initializing database")
        if os.path.exists("app.db"):
            os.remove("app.db")
        os.system("flask db init")
        os.system("flask db migrate")
        os.system("flask db upgrade")
