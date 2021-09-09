from gpcp.core.base_handler import buildHandlerFromFunction
from gpcp.utils.handlerValidator import validateHandler, validateNullableHandler
from gpcp.utils.errors import ConfigurationError
from gpcp.core.endpoint import EndPoint
from typing import Union, Callable
from gpcp.core import packet
import threading
import socket

import logging
logger = logging.getLogger(__name__)

class Server:
    """
    gpcp server main class, used for creating and using a server
    """

    def __init__(self, role = "R", handler: Union[type, Callable] = None, reuseAddress: bool = False):
        """
        Initialize server

        :param role: the role of the server endpoints
        :param handler: the handler class, usually extending utils.base_handler.BaseHandler
        :param reuseAddress: set if overwrite server on the same port with the current one
        """

        logger.debug(f"__init__() called with role={role}, handler={handler}, reuseAddress={reuseAddress}")

        if role not in ["R", "A", "AR", "RA"]:
            raise ConfigurationError(f"invalid role for {self.__class__.__name__}: options are ['A', 'R', 'RA' | 'AR']")
        self.role = role

        self.handler = validateNullableHandler(handler)

        self.connectedEndpoints = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)

        if not isinstance(reuseAddress, bool):
            raise ConfigurationError(f"invalid option '{reuseAddress}' for reuseAddress, must be 'True' or 'False'")
        if reuseAddress:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopServer()
        if exc_type is not None and exc_value is not None and exc_tb is not None:
            print(exc_type, "\n", exc_value, "\n", exc_tb)

    def setHandler(self, handler: Union[type, Callable]):
        """
        Sets the handler class used as a factory to instantiate a handler for every connection

        :param handler: the handler class, usually extending utils.base_handler.BaseHandler
        """

        logger.debug(f"setHandler() called with handler={handler}")

        self.handler = validateHandler(handler)

    def startServer(self, host: str, port: int, buffer: int = 5):
        """
        start the server and open it for connections

        :param host: address or ip to bind the server to
        :param port: port where bind the server
        :param buffer: how many connections can be buffered at the same time
        :returns: self
        """

        logger.info(f"startServer() called with host={host}, port={port}, buffer={buffer}")

        if not isinstance(host, str):
            raise ConfigurationError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ConfigurationError(f"invalid option '{port}' for port, must be integer")
        if not isinstance(buffer, int):
            raise ConfigurationError(f"invalid option '{buffer}' for buffer, must be integer")
        if self.handler is None:
            raise ConfigurationError(f"'startServer' can be used only after a handler is assigned")

        # start the server
        self.socket.bind((host, port))
        self.socket.listen(buffer)

        while True:
            try:
                connectionSocket, address = self.socket.accept()
                logger.info(f"new connection: {address}")

                # Create a new handler using handler as a factory.
                # The handler can store whatever information it wants relatively to a
                # connection, so it can't be used statically, but it must be instantiated
                handlerInstance = self.handler()

                # initializing the endpoint object and starting the thread
                endpoint = EndPoint(self, connectionSocket, self.role, handlerInstance)
                self.connectedEndpoints.append(endpoint)
            except BlockingIOError:
                pass # there is no connection yet

            for i, endpoint in enumerate(self.connectedEndpoints):
                if endpoint.isStopped():
                    logger.debug(f"connected endpoint thread {endpoint.mainLoopThread.name} is dead, deleting")
                    del self.connectedEndpoints[i]

        return self

    def closeConnection(self, host, port):
        """
        Closes a connection from a client

        :param host: ip address of connection to close
        :param port: port of connection to close
        """

        logger.info(f"closeConnection() called with host={host}, port={port}")

        deleted = False
        for i, endpoint in enumerate(self.connectedEndpoints):
            if endpoint.localAddress == (host, port):
                data = endpoint.handler.onDisonnected(self, endpoint.socket, endpoint.remoteAddress)
                if data is not None:
                    packet.sendAll(endpoint.socket, data)

                endpoint._closeConnection(True)
                del self.connectedEndpoints[i]
                deleted = True
                break

        if not deleted:
            raise ConfigurationError(f"{host}:{port} is not a connected endpoint of this server")

    def stopServer(self):
        """
        Shuts down the server
        """

        logger.info(f"stopServer() called")

        for endpoint in self.connectedEndpoints:
            self.closeConnection(endpoint.localAddress[0], endpoint.localAddress[1])

        try:
            self.socket.close()
        except OSError:
            # the server is not started so there isn't something to stop
            logger.warning("unable to correctly stop server, probably not started", exc_info=True)
