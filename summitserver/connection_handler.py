"""
Module represents a connection handler to parse and process user requests.
"""
import json
import logging
import traceback
import socket

from typing import Optional

from .optimization_handler import OptimizationHandler


DEFAULT_BUFFER_SIZE = 4096

class Handler:

    def __init__(self) -> None:

        self.logger: logging.Logger = logging.getLogger(
            'summit-server.handler')

        self.connections: set[socket.socket] = set()
        self.optimizations: dict[str, OptimizationHandler] = {}

    def register_connection(self, connection: socket.socket) -> None:
        """ Registering the connection. """

        self.connections.add(connection)
        self.logger.info('Connection from %s registered.',
                         connection.getpeername())

    def register_request(self, request: dict) -> None:
        """ Registering the request with the optimization hash. """
        self.optimizations.update({
            f'{request["hash"]}': OptimizationHandler(request)
            })
        self.logger.info('Registered request with %s hash', request['hash'])

    def handle_request(self, request: bytes) -> bytes:
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

    def __call__(self, connection: socket.socket) -> bool:
        """Call method to handle the connection.

        Register it as a new one, if not registered; process incoming message.

        Args:
            connection (socket.socket): Incoming connection.

        Returns:
            bool: True if the connection was closed or reset, False if processed
                okay.
        """
        if connection not in self.connections:
            self.register_connection(connection)

        try:
            request = connection.recv(DEFAULT_BUFFER_SIZE)

        except ConnectionResetError:
            self.logger.info('Connection <%s> reset', connection)
            connection.close()
            return True

        if not request:
            self.logger.info('Connection %s closed', connection)
            connection.close()
            return True

        reply = self.handle_request(request)
        connection.sendall(reply)

        return False
