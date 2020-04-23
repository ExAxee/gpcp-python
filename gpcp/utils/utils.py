"""utilities module containing all function used by more than one script"""

def sendAll(connection, data):
    """sends all data, this is not the default socket.sendall() function"""

    if isinstance(data, bytes):
        data = f"{len(data):<{HEADER}}".encode(ENCODING) + data
    else:
        data = (f"{len(data):<{HEADER}}" + data).encode(ENCODING)

    while data:
        sent = connection.send(data)
        data = data[sent:]

class Packet:
    """Packet object"""
    
    HEADER = 8
    ENCODING = "utf-8"