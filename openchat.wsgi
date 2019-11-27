activate = '/var/www/openchat/venv/bin/activate_this.py'
with open(activate) as f:
	exec(f.read(), dict(__file__=activate))

import sys, logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/openchat/')

from run import app as application