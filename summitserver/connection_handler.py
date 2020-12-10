"""
Module represents a connection handler to parse and process user requests.
"""
import json
import logging

from .utils.logger import get_logger
from .optimization_handler import OptimizationHandler


class Handler:

    def __init__(self):

        self.logger = get_logger('handler', logging.INFO, None)

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
        if request['hash'] not in self.optimizations:
            self.register_request(request)
        reply = self.optimizations[request['hash']](request)
        reply = bytes(json.dumps(reply), encoding='ascii')

        return reply

    def __call__(self, connection):
        if connection not in self.connections:
            self.register_connection(connection)
        request = connection.recv(1024)
        if not request:
            connection.close()
            return
        reply = self.handle_request(request)
        connection.sendall(reply)
