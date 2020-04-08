import socket

class Server:
    HEADER = 4

    def __init__(self, reuse_addr=False):
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if isinstance(reuse_addr, bool):
            if reuse_addr:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            raise ValueError(f"invalid option '{reuse_addr}' for reuse_adrr, must be True or False")

    def startServer(self, IP, port, data_request_trigger, connection_request_trigger=None, buffer=5):
        """start the server and open it for connections."""

        if not isinstance(IP, str):
            raise ValueError(f"invalid option '{IP}' for IP, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")
        if not callable(data_request_trigger):
            raise ValueError(f"invalid option '{data_request_trigger}' for data_request_trigger, must be callable")
        if connection_request_trigger is not None and not callable(connection_request_trigger):
            raise ValueError(f"invalid option '{connection_request_trigger}' for connection_request_trigger, must be callable")
        if not isinstance(buffer, int):
            raise ValueError(f"invalid option '{buffer}' for buffer, must be integer")

        self.socket.bind( (IP, port) )
        self.socket.listen(buffer)

        while True:
            connection, address = self.socket.accept()
            self.connections.append( (connection, address) )
            if connection_request_trigger != None:
                connection_request_trigger(connection, address)

            for connection in self.connections:
                head = connection[0].recv(Server.HEADER) #read the header from a buffered request
                byteCount = int(head)
                data = connection[0].recv(byteCount) #read the actual message of len head

                while len(data) < byteCount:
                    data += connection[0].recv( byteCount - len(data) )

                response = data_request_trigger(data, connection)

                if isinstance(response, bytes):
                    connection[0].sendall(f"{len(response):<{Server.HEADER}}".encode("utf-8") + response)
                else:
                    connection[0].sendall((f"{len(response):<{Server.HEADER}}" + response).encode("utf-8"))

    def closeConnection(self, connection, msg = None):
        """closes a connection from a client, if msg is specified the server will send that msg and after will close the connection"""

        if msg:
            if not isinstance(msg, str):
                raise ValueError(f"invalid option '{msg}' for msg, must be string")

        if (connection, connection.getpeername() ) not in self.connections:
            raise ValueError(f"connection {connection.getsockname()} is not a connection of this server")
        if msg:
            connection.send((f"{len(msg):<{Server.HEADER}}" + msg).encode("utf-8"))
        self.connections.remove( (connection, connection.getpeername() ) )
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()

    def stopServer(self):
        """Shuts down the server"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def __del__(self):
        self.stopServer()
