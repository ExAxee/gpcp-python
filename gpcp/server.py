from gpcp.core.base_handler import buildHandlerFromFunction
from gpcp.utils.handlerValidator import validateHandler
from gpcp.utils.errors import ConfigurationError
from gpcp.core.connection import Connection
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
        start the server and open it for connections

        :param host: address or ip to bind the server to
        :param port: port where bind the server
        :param buffer: how many connections can be buffered at the same time
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
                #initializing the endpoint
                endpoint = EndPoint(connectionSocket, self._gpcpRole, handler)

                #setting up the endpoint thread
                thread = threading.Thread(target=endpoint.mainLoop)
                thread.setName(f"connection ({address[0]}:{address[1]})")

                #initializing the connection object and starting the thread
                connection = Connection(endpoint, thread)
                connection.thread.start()

                endpoint.handler.onConnected(self, endpoint, address)
                self.connections.append(connection)
            except BlockingIOError:
                pass # there is no connection yet

            for i, connection in enumerate(self.connections):
                if not connection.thread.is_alive():
                    logger.debug(f"connection thread {connection.thread.name} is dead, deleting")
                    del self.connections[i]

    def closeConnection(self, host, port):
        """
        Closes a connection from a client

        :param ip: ip address of connection to close
        :param port: port of connection to close
        """

        logger.info(f"closeConnection() called with host={host}, port={port}")

        deleted = False
        for i, connection in enumerate(self.connections):
            if connection.endpoint.localAddress == (host, port):
                data = connection.endpoint.handler.onDisonnected(self, connection.endpoint.socket, connection.endpoint.remoteAddress)
                if data is not None:
                    packet.sendAll(connection.socket, data)

                del self.connections[i]
                deleted = True
                break

        if not deleted:
            raise ConfigurationError(
                f"connection {connection.endpoint.socket.getsockname()} is not a connection of this server"
            )

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
            #does not need exception info as the error is cause by the absence of the 'socket' var
            logger.warning("unable to correctly stop server, socket not initialized")
            pass
        except OSError: #the server is not started so there isn't something to stop
            logger.warning("unable to correctly stop server, probably not started", exc_info=True)
            pass

    def __init__(self, role = "R", handler: Union[type, Callable] = None, reuseAddress: bool = False):
        """
        Initialize server

        :param handler: a class or a function to call on requests
        :param reuseAddress: set if overwrite server on the same port with the current one
        """

        if role == "R":
            self._gpcpRole = role
        elif role == "A":
            self._gpcpRole = role
        elif role == "AR" or role == "RA":
            self._gpcpRole = role
        else:
            raise ConfigurationError(f"invalid server role for {self.__class__.__name__}: options are ['A', 'R', 'RA' | 'AR']")

        logger.debug(f"__init__() called with handler={handler}, reuseAddress={reuseAddress}")

        if handler:
            self.setHandler(handler)
        else:
            self.handler = None
        self.connections = []
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
