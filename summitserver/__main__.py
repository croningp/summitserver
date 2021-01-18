""" Initialize SummitServer and run its main loop. """

import atexit
import argparse

from summitserver import SummitServer

DEFAULT_HOST = 'dragonsoop2'
DEFAULT_PORT = 12111

parser = argparse.ArgumentParser()
parser.add_argument('--host', metavar='HOST', type=str, default=DEFAULT_HOST)
parser.add_argument('-p', '--port', metavar='PORT', type=int, default=DEFAULT_PORT)

args = vars(parser.parse_args())

if args['host'] != DEFAULT_HOST:
    SummitServer.HOST = args['host']

ss = SummitServer(args['port'])
try:
    ss.main()
except Exception as e:
    print('\nException happened, interrupting.')
    ss.server.close()
    print('Server closed')
    raise e
