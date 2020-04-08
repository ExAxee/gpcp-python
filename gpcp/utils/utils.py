"""utilities module containing all function used by more than one script"""

HEADER = 4

def sendAll(connection, data):
    """sends all data, this is not the default socket.sendall() function"""
    
    if isinstance(data, bytes):
        data = f"{len(data):<{HEADER}}".encode("utf-8") + data
    else:
        data = (f"{len(data):<{HEADER}}" + data).encode("utf-8")
    
    while data:
        sent = connection.send(data)
        data = data[sent:]