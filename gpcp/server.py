import socket
from typing import Union, Callable
from gpcp.core.base_handler import buildHandlerFromFunction
from gpcp.core import packet
from gpcp.core.connection import Connection
from gpcp.utils.errors import ConfigurationError

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

        #check for handleData core function
        if not hasattr(handler, "handleData"):
            # suppose this is a function
            if not callable(handler):
                raise ConfigurationError(
                    f"{handler.__name__} is neither a handler class nor a function"
                )
            self.handler = buildHandlerFromFunction(handler)
            return
        elif hasattr(handler, "handleData"):
            # this has to be a handler class
            if not callable(handler.handleData):
                raise ConfigurationError(
                    f"invalid core method in '{handler.__name__}' for handler class: 'handleData' is not callable"
                )
        else:
            raise ConfigurationError(
                f"missing core method in '{handler.__name__}' for handler class, missing function 'handleData'"
            )

        # check for loadHandlers core function
        if hasattr(handler, "loadHandlers"):

            # start the handlers loading
            if callable(handler.loadHandlers):
                self.handler = handler
                self.handler.loadHandlers()
            else:
                raise ConfigurationError(
                    f"invalid core method in '{handler.__name__}' for handler class, 'loadHandlers' is not callable"
                )
        else:
            raise ConfigurationError(
                f"missing core method in '{handler.__name__}' for handler class, missing function 'loadHandlers'"
            )

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
                connection, address = self.socket.accept()
                logger.info(f"new connection: {address}")
                connection.setblocking(False)

                # Create a new handler using handler as a factory.
                # The handler can store whatever information it wants relatively to a
                # connection, so it can't be used statically, but it must be instantiated
                handler = self.handler()
                handler.onConnected(self, connection, address)
                self.connections.append(Connection(connection, address, handler))
            except BlockingIOError:
                pass # there is no connection yet

            for singleConnection in self.connections:
                try:
                    data = packet.receiveAll(singleConnection.socket)
                    if data is None: # connection was closed
                        logger.info(f"received None data from {address}, closing connection: ")
                        self.closeConnection(singleConnection.host, singleConnection.port)
                    else: # send the handler response to the client
                        logger.debug(f"received data from {address}")
                        packet.sendAll(singleConnection.socket, singleConnection.handler.handleData(data))
                except BlockingIOError:
                    continue

    def closeConnection(self, host, port):
        """
        Closes a connection from a client

        :param ip: ip address of connection to close
        :param port: port of connection to close
        """

        logger.info(f"closeConnection() called with host={host}, port={port}")

        deleted = False
        for i, connection in enumerate(self.connections):
            if connection.host == host and connection.port == port:
                data = connection.handler.onDisonnected(self, connection.socket, (connection.host, connection.port))
                if data is not None:
                    packet.sendAll(connection.socket, data)

                del self.connections[i]
                deleted = True
                break

        if not deleted:
            raise ConfigurationError(
                f"connection {connection.socket.getsockname()} is not a connection of this server"
            )

        connection.socket.shutdown(socket.SHUT_RDWR)
        connection.socket.close()

    def stopServer(self):
        """
        Shuts down the server
        """

        logger.info(f"stopServer() called")

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except OSError: #the server is not started so there isn't something to stop
            logger.warning("unable to correctly stop server, probably not started", exc_info=True)
            pass

    def __init__(self, handler: Union[type, Callable] = None, reuseAddress: bool = False):
        """
        Initialize server

        :param handler: a class or a function to call on requests
        :param reuseAddress: set if overwrite server on the same port with the current one
        """

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
