class Connection():

    def __init__(self, connection, address, handler):
        self.socket = connection
        self.host = address[0]
        self.port = address[1]
        self.handler = handler