import sys, logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/openchat/')

activate_this = '/var/www/openchat/venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), dict(__file__=activate_this))

from app import create_app
application = create_app()