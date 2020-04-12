"""utilities module containing all function used by more than one script"""

HEADER = 4
ENCODING = "utf-8"

def sendAll(connection, data):
    """sends all data, this is not the default socket.sendall() function"""

    if isinstance(data, bytes):
        data = f"{len(data):<{HEADER}}".encode(ENCODING) + data
    else:
        data = (f"{len(data):<{HEADER}}" + data).encode(ENCODING)

    while data:
        sent = connection.send(data)
        data = data[sent:]