import socket

global HEADER
HEADER = 4

class Server:
    self.__triggers = []
    self.connections = []
    
    def __init__(self,
                 reuse_addr=False: bool):        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if reuse_addr:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def startserver(self, IP: str, trigger_conn: callable, trigger_data: callable, buffer=5: int, port=7530: int):
        self.socket.bind( (IP, port) )
        self.socket.listen(buffer)
    
        while True:
            connection, address = self.socket.accept()
            trigger_conn(connection, address)
            data, address = self.socket.recvfrom(HEADER)
            data, address = 
    
    """
    def on_connection_request(self, func):
        connection, address = self.socket.accept()
        func(connection, address)
    
    def on_recieve(self, func, mode=1: int):
        """mode 1 = recieve bytes, mode 2 = recieve bytes and address"""
        data, address = self.socket.recvfrom(10)
        
    
    def add_handler(self, func: callable, trigger: str):
        pass
        
        while 1:
            clientsocket, address = self.socket.accept()
            print(f"Connection with {address} established.")
            
            self.msg = "Welcome to the server!"
            self.msg = f"{len(self.msg):<{HEADER}}" + self.msg
            clientsocket.send(bytes(self.msg,"utf-8"))
            
            while 1:
                self.msg = str(input("string to send >>> "))
                self.msg = f"{len(self.msg):<{HEADER}}" + self.msg
                clientsocket.send(bytes(self.msg,"utf-8"))
    """