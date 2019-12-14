import sys, logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/openchat/')

from run import app as application