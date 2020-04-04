import socket

global HEADER
HEADER = 4

class Server:
    self.connections = []
    
    def __init__(self,
                 reuse_addr=False: bool):        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def startServer(self,
                    IP: str,
                    port=7530: int,
                    data_request_trigger: callable,
                    connection_request_trigger=None: callable,
                    buffer=5: int):
        
        self.socket.bind( (IP, port) )
        self.socket.listen(buffer)
    
        while True:
            connection, address = self.socket.accept()
            self.connections.append( (connection, address) )
            if connection_request_trigger != None:
                connection_request_trigger(connection, address)
            
            head, address = self.socket.recvfrom(HEADER)
            data, address = self.socket.recvfrom(int(head))
            data_request_trigger(data, address)
    
    def closeConnection(connection, msg = None: str):
        """closes a connection from a client, if msg is specified the server will send that msg and after will close the connection"""
        if msg:
            connection.send(bytes(
                f"{len(msg):<{HEADER}}" + msg
                ))
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()
    
    def stopServer():
        """Shuts down the server"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()