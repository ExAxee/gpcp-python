import socket

global HEADER
HEADER = 4

class Server:
    
    def __init__(self,
                 reuse_addr=False: bool):
        self.connections = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def startServer(self,
                    IP: str,
                    port=7530: int,
                    data_request_trigger: callable,
                    connection_request_trigger=None: callable,
                    buffer=5: int):
        """start the server and open it for connections."""
        
        self.socket.bind( (IP, port) )
        self.socket.listen(buffer)
    
        while True:
            connection, address = self.socket.accept()
            self.connections.append( (connection, address) )
            if connection_request_trigger != None:
                connection_request_trigger(connection, address)
            
            for connection in self.connections:
                head = connection[0].recv(HEADER)
                data = connection[0].recv(int(head))
                response = data_request_trigger(data, connection)
                
                if isinstance(response, bytes):
                    connection.sendall(f"{len(response):<{HEADER}}" + response)
                else:
                    connection.sendall(bytes(f"{len(response):<{HEADER}}" + response))
    
    def closeConnection(self, connection, msg = None: str):
        """closes a connection from a client, if msg is specified the server will send that msg and after will close the connection"""
        if msg:
            connection.send(bytes(
                f"{len(msg):<{HEADER}}" + msg
                ))
        self.connections.remove( (connection, connection.getpeername() ) )
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()
    
    def stopServer(self):
        """Shuts down the server"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    
    def __del__(self):
        self.stopServer()