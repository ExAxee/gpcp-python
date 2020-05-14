import socket
from gpcp.utils.base_handler import buildHandlerFromFunction
from gpcp.utils import packet

class Server:

    def __init__(self, handler=None, reuse_addr: bool = False):
        if handler:
            self.setHandler(handler)
        else:
            self.handler = None
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)

        if not isinstance(reuse_addr, bool):
            raise ValueError(f"invalid option '{reuse_addr}' for reuse_addr, must be True or False")
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        return self

    def setHandler(self, handler: type or callable):
        """
        Sets the handler class used as a factory to instantiate a handler for every connection
            :param handler: the handler class, usually extending BaseHandler
        """

        if not hasattr(handler, "handleData"):
            # suppose this is a function
            if not callable(handler):
                raise ValueError(f"'{handler}' is neither a handler class nor a function")
            self.handler = buildHandlerFromFunction(handler)
            return

        # this has to be a handler class
        if not callable(handler.handleData):
            raise ValueError(f"missing core method in '{handler}' for handler class:"
                             + " 'handleData' is not callable")

        if hasattr(handler, "loadHandlers"):
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
        """start the server and open it for connections."""

        if not isinstance(IP, str):
            raise ValueError(f"invalid option '{IP}' for IP, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")
        if not isinstance(buffer, int):
            raise ValueError(f"invalid option '{buffer}' for buffer, must be integer")
        if self.handler is None:
            raise ValueError(f"'startServer' can be used only after a handler is assigned")

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

    def closeConnection(self, connection, msg=None):
        """
        Closes a connection from a client, if `msg` is specified
        the server will send it and afterwards close the connection
        """

        if msg:
            if not isinstance(msg, str) and not isinstance(msg, bytes):
                raise ValueError(f"invalid option '{msg}' for msg, must be string")

        if msg:
            packet.sendAll(connection, msg)

        deleted = False
        for i in range(len(self.connections)):
            if self.connections[i][0] is connection:
                del self.connections[i]
                deleted = True
                break
        if not deleted:
            raise ValueError(
                f"connection {connection.getsockname()} is not a connection of this server")

        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

    def stopServer(self):
        """Shuts down the server"""
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except OSError: #the server is not started so there isn't something to stop
            pass

    def __del__(self):
        self.stopServer()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopServer()
        if exc_type and exc_value and exc_tb is not None:
            print(exc_type, "\n", exc_value, "\n", exc_tb)
