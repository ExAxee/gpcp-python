"""packet module containing functions to handle packets"""
import json

HEADER_LENGTH = 4
HEADER_BYTEORDER = "big"
ENCODING = "utf-8"

def commandToData(commandIdentifier: str, arguments: list):
    return (commandIdentifier + json.dumps(arguments)).encode(ENCODING)

def dataToCommand(data: bytes):
    data = data.decode(ENCODING)
    separatorIndex = data.find("[")
    commandIdentifier = data[:separatorIndex]
    arguments = json.loads(data[separatorIndex:])
    return (commandIdentifier, arguments)

def sendAll(connection, data):
    """sends all data, this is not the default socket.sendall() function"""
    print("Sending", data)

    if isinstance(data, str):
        data = data.encode(ENCODING)

    data = len(data).to_bytes(HEADER_LENGTH, byteorder=HEADER_BYTEORDER) + data
    while data:
        sent = connection.send(data)
        data = data[sent:]

def receiveAll(connection):
    head = connection.recv(HEADER_LENGTH) #read the header from a buffered request

    byteCount = int.from_bytes(head, byteorder=HEADER_BYTEORDER)
    data = connection.recv(byteCount) #read the actual message of len head

    while len(data) < byteCount:
        data += connection.recv(byteCount - len(data))

    print("Received", data)
    return data
