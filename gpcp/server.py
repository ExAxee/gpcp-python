import socket
from typing import Union, Callable
from gpcp.utils.base_handler import buildHandlerFromFunction
from gpcp.utils import packet

class Server:
    """
    gpcp server main class, used for creating and using a server
    """

    def setHandler(self, handler: Union[type, Callable]):
        """
        Sets the handler class used as a factory to instantiate a handler for every connection

        :param handler: the handler class, usually extending utils.base_handler.BaseHandler
        """

        if not hasattr(handler, "handleData"):
            # suppose this is a function
            if not callable(handler):
                raise ValueError(f"'{handler}' is neither a handler class nor a function")
            self.handler = buildHandlerFromFunction(handler)
            return

        # this has to be a handler class
        if not callable(handler.handleData):
            raise ValueError(f"invalid core method in '{handler}' for handler class:"
                             + " 'handleData' is not callable")

        # check for core function
        if hasattr(handler, "loadHandlers"):

            # start the handlers loading
            if callable(handler.loadHandlers):
                self.handler = handler
                self.handler.loadHandlers()
            else:
                raise ValueError(f"invalid core method in '{handler}' for handler class,"
                                 + " 'loadHandlers' is not callable")
        else:
            raise ValueError(f"missing core method in '{handler}' for handler class,"
                             + " missing function 'loadHandlers'")

    def startServer(self, IP: str, port: int, buffer: int = 5):
        """
        start the server and open it for connections

        :param IP: address or ip where bind the server
        :param port: port where bind the server
        :param buffer: how many connections can be buffered at the same time
        """

        if not isinstance(IP, str):
            raise ValueError(f"invalid option '{IP}' for IP, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")
        if not isinstance(buffer, int):
            raise ValueError(f"invalid option '{buffer}' for buffer, must be integer")
        if self.handler is None:
            raise ValueError(f"'startServer' can be used only after a handler is assigned")

        # start the server
        self.socket.bind((IP, port))
        self.socket.listen(buffer)

        while True:
            try:
                connection, address = self.socket.accept()
                connection.setblocking(False)

                # Create a new handler using handler as a factory.
                # The handler can store whatever information it wants relatively to a
                # connection, so it can't be used statically, but it must be instantiated
                handler = self.handler()
                handler.onConnected(self, connection, address)
                self.connections.append((connection, address, handler))
            except BlockingIOError:
                pass # there is no connection yet

            for sock, address, handler in self.connections:
                try:
                    data = packet.receiveAll(sock)
                    if data is None: # connection was closed
                        self.closeConnection(sock)
                    else: # send the handler response to the client
                        packet.sendAll(sock, handler.handleData(data))
                except BlockingIOError:
                    continue

    def closeConnection(self, connectionToDelete):
        """
        Closes a connection from a client

        :param connectionToDelete: connection to close
        """

        deleted = False
        for i, connection in enumerate(self.connections):
            if connection[0] is connectionToDelete:
                data = connection[2].onDisonnected(self, connection[0], connection[1])
                if data is not None:
                    packet.sendAll(connection[0], data)

                del self.connections[i]
                deleted = True
                break

        if not deleted:
            raise ValueError(
                f"connection {connectionToDelete.getsockname()} is not a connection of this server")

        connectionToDelete.shutdown(socket.SHUT_RDWR)
        connectionToDelete.close()

    def stopServer(self):
        """
        Shuts down the server
        """

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except OSError: #the server is not started so there isn't something to stop
            pass

    def __init__(self, handler: Union[type, Callable] = None, reuse_addr: bool = False):
        """
        Initialize server

        :param handler: a class or a function to call on requests
        :param reuse_addr: set if overwrite server on the same port with the current one
        """

        if handler:
            self.setHandler(handler)
        else:
            self.handler = None
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)

        if not isinstance(reuse_addr, bool):
            raise ValueError(f"invalid option '{reuse_addr}' for reuse_addr, must be 'True' or 'False'")
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopServer()
        if exc_type and exc_value and exc_tb is not None:
            print(exc_type, "\n", exc_value, "\n", exc_tb)

    def __del__(self):
        self.stopServer()
