import socket
from gpcp.utils import packet

class Server:

    def __init__(self, reuse_addr: bool = False):
        self.handlerClass = None
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)

        if not isinstance(reuse_addr, bool):
            raise ValueError(f"invalid option '{reuse_addr}' for reuse_addr, must be True or False")
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        return self

    def setHandlerClass(self, handlerClass: type):
        """
        Sets the handler class used as a factory to instantiate a handler for every connection
            :param handlerClass: the handler class, usually extending BaseHandler
        """
        self.handlerClass = handlerClass

        if hasattr(handlerClass, "loadHandlers"):
            if callable(handlerClass.loadHandlers):
                self.handlerClass.loadHandlers()
            else:
                raise ValueError(f"invalid option '{handlerClass}' for handler class,"
                                 + " 'loadHandlers' is not callable")
        if not hasattr(handlerClass, "handleData") or not callable(handlerClass.handleData):
            raise ValueError(f"invalid option '{handlerClass}' for handler class,"
                             + " missing function 'handleData'")

    def startServer(self, IP: str, port: int, buffer: int = 5):
        """start the server and open it for connections."""

        if not isinstance(IP, str):
            raise ValueError(f"invalid option '{IP}' for IP, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")
        if not isinstance(buffer, int):
            raise ValueError(f"invalid option '{buffer}' for buffer, must be integer")
        if self.handlerClass is None:
            raise ValueError(f"'startServer' can be used only after 'setHandlerClass' was called")

        self.socket.bind((IP, port))
        self.socket.listen(buffer)

        while True:
            try:
                connection, address = self.socket.accept()
                connection.setblocking(False)

                # Create a new handler using handlerClass as a factory.
                # The handler can store whatever information it wants relatively to a
                # connection, so it can't be used statically, but it must be instantiated
                handler = self.handlerClass()
                self.connections.append((connection, address, handler))
            except BlockingIOError:
                pass # there is no connection yet

            for sock, address, handler in self.connections:
                try:
                    data = packet.receiveAll(sock)
                    if data is not None:
                        # tell the handler for the current connection about the received command
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
        if (connection, connection.getpeername()) not in self.connections:
            raise ValueError(
                f"connection {connection.getsockname()} is not a connection of this server")

        if msg:
            packet.sendAll(connection, msg)

        self.connections.remove((connection, connection.getpeername()))
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

    def stopServer(self):
        """Shuts down the server"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def __del__(self):
        self.stopServer()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopServer()
        if exc_type and exc_value and exc_tb is not None:
            print(exc_type, "\n", exc_value, "\n", exc_tb)
