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

    def setHandler(self, handler: Union[type, Callable]):
        """
        Sets the handler class used as a factory to instantiate a handler for every connection

        :param handler: the handler class, usually extending utils.base_handler.BaseHandler
        """

        logger.debug(f"setHandler() called with handler={handler}")

        self.handler = validateHandler(handler)

    def startServer(self, host: str, port: int, buffer: int = 5):
        """
        start the server and open it for connectedEndpoints

        :param host: address or ip to bind the server to
        :param port: port where bind the server
        :param buffer: how many connectedEndpoints can be buffered at the same time
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
                handler = self.handler()

                # initializing the endpoint object and starting the thread
                endpoint = EndPoint(connectionSocket, self.role, handler)
                endpoint.startMainLoopThread()
                self.connectedEndpoints.append(endpoint)

                # notifying the handler of the new connection
                endpoint.handler.onConnected(self, endpoint, address)
            except BlockingIOError:
                pass # there is no connection yet

            for i, endpoint in enumerate(self.connectedEndpoints):
                if not endpoint.thread.is_alive():
                    logger.debug(f"connected endpoint thread {endpoint.thread.name} is dead, deleting")
                    del self.connectedEndpoints[i]

    def closeConnection(self, host, port):
        """
        Closes a connection from a client

        :param host: ip address of connection to close
        :param port: port of connection to close
        """

        logger.info(f"closeConnection() called with host={host}, port={port}")

        deleted = False
        for i, endpoint in enumerate(self.connectedEndpoints):
            if endpoint.endpoint.localAddress == (host, port):
                data = endpoint.endpoint.handler.onDisonnected(self, endpoint.endpoint.socket, endpoint.endpoint.remoteAddress)
                if data is not None:
                    packet.sendAll(endpoint.socket, data)

                del self.connectedEndpoints[i]
                deleted = True
                break

        if not deleted:
            raise ConfigurationError(f"{host}:{port} is not a connected endpoint of this server")

        connection.endpoint.socket.shutdown(socket.SHUT_RDWR)
        connection.endpoint.socket.close()

    def stopServer(self):
        """
        Shuts down the server
        """

        logger.info(f"stopServer() called")

        try:
            self.socket.close()
        except AttributeError:
            # does not need exception info as the error is cause by the absence of the 'socket' var
            logger.warning("unable to correctly stop server, socket not initialized")
            pass
        except OSError:
            # the server is not started so there isn't something to stop
            logger.warning("unable to correctly stop server, probably not started", exc_info=True)
            pass

    def __init__(self, role = "R", handler: Union[type, Callable] = None, reuseAddress: bool = False):
        """
        Initialize server

        :param handler: a class or a function to call on requests
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

    def __del__(self):
        self.stopServer()
