from .utils.utils import sendAll, HEADER, ENCODING
from .utils.base_handler import BaseHandler
import socket

class Server:

    def __init__(self, reuse_addr=False):
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        if isinstance(reuse_addr, bool):
            if reuse_addr:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            raise ValueError(f"invalid option '{reuse_addr}' for reuse_adrr, must be True or False")

    def startServer(self, IP: str, port: int, handlerClass, buffer: int = 5):
        """start the server and open it for connections."""

        if not isinstance(IP, str):
            raise ValueError(f"invalid option '{IP}' for IP, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")
        if not isinstance(buffer, int):
            raise ValueError(f"invalid option '{buffer}' for buffer, must be integer")

        self.socket.bind( (IP, port) )
        self.socket.listen(buffer)

        while True:
            try:
                connection, address = self.socket.accept()
                connection.setblocking(False)
                handler = handlerClass()
                self.connections.append( (connection, address, handler) )
            except BlockingIOError:
                pass # there is no connection yet

            for sock, address, handler in self.connections:
                try:
                    head = sock.recv(HEADER) #read the header from a buffered request
                except BlockingIOError:
                    continue

                if head:
                    byteCount = int(head)
                    data = sock.recv(byteCount) #read the actual message of len head

                    while len(data) < byteCount:
                        data += sock.recv( byteCount - len(data) )

                    handler.handleCommand(data)
                    sendAll(sock, b"")

    def closeConnection(self, connection, msg = None):
        """closes a connection from a client, if msg is specified the server will send that msg and after will close the connection"""

        if msg:
            if not isinstance(msg, str):
                raise ValueError(f"invalid option '{msg}' for msg, must be string")

        if (connection, connection.getpeername() ) not in self.connections:
            raise ValueError(f"connection {connection.getsockname()} is not a connection of this server")
        if msg:
            connection.send((f"{len(msg):<{HEADER}}" + msg).encode(ENCODING))
        self.connections.remove( (connection, connection.getpeername() ) )
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

    def stopServer(self):
        """Shuts down the server"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def __del__(self):
        self.stopServer()
