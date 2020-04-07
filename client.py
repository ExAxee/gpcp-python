import socket

class Client:
    HEADER = 4
    
    def __init__(self, default_handler=None: callable):
        """if default_handler is specified all responses to all requests will be handled by this callable"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host: str, port: int):
        self.socket.connect( (host, port) )
    
    def request(self, request, handler=None: callable):
        """if handler is specified it will overwrite temporairly the default_handler"""
        
        if isinstance(request, bytes): 
            self.socket.sendall(bytes(f"{len(request):<{HEADER}}") + request)
        else:
            self.socket.sendall(bytes(f"{len(request):<{HEADER}}" + request))
        
        head = self.socket.recv(HEADER) #read the header from a buffered request
        data = self.socket.recv(int(head)) #read the actual message of len head
        
        while len(data) < head:
            data += self.socket.recv( int(head) - len(data) )
        
        if handler != None:
            handler(self.socket, data)
        elif default_handler != None:
            default_handler(self.socket, data)
        else:
            return data
    
    def closeConnection(self, mode = "RW": str):
        """closes the connection to the server, RW = read and write, R = read, W = write"""
        if mode == "RW":
            self.socket.shutdown(socket.SHUT_RDWR)
        elif mode == "R":
            self.socket.shutdown(socket.SHUT_RD)
        elif mode == "W":
            self.socket.shutdown(socket.SHUT_WR)
        else:
            raise ValueError("close mode must be 'R' or 'W' or 'RW'")
        
        self.socket.close()

