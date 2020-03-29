import os
import click
from app import db


def register(cli):
    @cli.command()
    def init():
        print("Initializing database...")
        if os.path.exists("app.db"):
            os.remove("app.db")
        db.create_all()

    @cli.command()
    def populate():
        print("Populating database...")
        from app import populate


if __name__ == '__main__':
    @click.group()
    def main_cli():
        pass

    register(main_cli)

    main_cli()

