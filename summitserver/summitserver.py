"""
Server wrapper of the Summit benchmarking library
(https://github.com/sustainable-processes/summit).
"""
import selectors
import socket

from .utils.logger import get_logger
from .connection_handler import Handler


class SummitServer:
    """ TCPIP server to allow communication with the Summit benchmarking module.
    """

    HOST = 'dragonsoop2'

    def __init__(self, port=12111):

        self.logger = get_logger()

        self.selector = selectors.DefaultSelector()

        self.server = self.start_server(port)

        self.handler = Handler()

    def start_server(self, port):
        """ Starts a TCPIP socket, listening at "dragonsoop2" and given port.
        """

        self.logger.info('Starting server at %s:%d', self.HOST, port)

        server = socket.socket()
        server.bind((self.HOST, port))
        server.listen(5)
        server.setblocking(False)

        self.selector.register(server, selectors.EVENT_READ, data=1)

        self.logger.debug('Server <%s> registered', server)

        return server

    def accept(self, sock, mask):
        """ Accepts incoming connection and register the corresponding socket
            in the selector. """

        conn, addr = sock.accept()
        self.logger.info('Accepted connection from %s, mask %d', addr, mask)
        conn.setblocking(False)
        events = selectors.EVENT_READ
        self.selector.register(conn, events, data=2)

    def main(self):
        """ Main loop, wait on available events and service incoming
            connections. """
        self.logger.info('Running main loop')
        while True:
            events = self.selector.select()
            self.logger.debug('Available events - %s', events)
            for key, mask in events:
                if key.data == 1: # incoming connection
                    self.logger.debug('Incoming connection %s', key)
                    self.accept(key.fileobj, mask)
                elif key.data == 2: # incoming message over connection
                    self.logger.debug('Read ready %s', key)
                    self.handler(key.fileobj)