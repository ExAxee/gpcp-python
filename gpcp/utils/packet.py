"""packet module containing functions to handle packets"""

HEADER = 8
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

def receiveAll(connection):
    head = connection.recv(HEADER) #read the header from a buffered request

    if head:
        byteCount = int(head)
        data = connection.recv(byteCount) #read the actual message of len head

        while len(data) < byteCount:
            data += connection.recv(byteCount - len(data))

        return data
    return None
