class Connection():
    
    def __init__(self, connection, address, handler):
        self.socket = connection
        self.ip = address[0]
        self.port = address[1]
        self.handler = handler