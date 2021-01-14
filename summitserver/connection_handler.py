"""
Module represents a connection handler to parse and process user requests.
"""
import json
import logging
import traceback

from .optimization_handler import OptimizationHandler


class Handler:

    def __init__(self):

        self.logger = logging.getLogger('summit-server.handler')

        self.connections = set()
        self.optimizations = {}

    def register_connection(self, connection):
        """ Registering the connection. """

        self.connections.add(connection)
        self.logger.info('Connection from %s registered.',
                         connection.getsockname())

    def register_request(self, request):
        """ Registering the request with the optimization hash. """
        self.optimizations.update({
            f'{request["hash"]}': OptimizationHandler(request)
            })
        self.logger.info('Registered request with %s hash', request['hash'])

    def handle_request(self, request):
        """ Invoking OptimizationHandler to process the incoming request. """
        request = json.loads(request.decode())
        try:
            if request['hash'] not in self.optimizations:
                self.register_request(request)
            reply = self.optimizations[request['hash']](request)
        except: # pylint: disable=bare-except
            tb = traceback.format_exc()
            reply = {'exception': tb}
        reply = bytes(json.dumps(reply), encoding='ascii')

        return reply

    def __call__(self, connection):
        if connection not in self.connections:
            self.register_connection(connection)
        try:
            request = connection.recv(1024)
        except ConnectionResetError:
            self.logger.info('Connection <%s> reset',
                              connection.getsockname())
            connection.close()
            return True
        if not request:
            self.logger.info('Connection from %s closed',
                             connection.getsockname())
            connection.close()
            return True
        reply = self.handle_request(request)
        connection.sendall(reply)
