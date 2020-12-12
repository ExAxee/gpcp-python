"""packet module containing functions to handle packets"""
from typing import Union, Tuple
import json

HEADER_LENGTH = 4
HEADER_BYTEORDER = "big"
ENCODING = "utf-8"

class CommandData:

    @staticmethod
    def encode(commandIdentifier: str, arguments: list) -> bytes:
        """
        formats the request from a user-friendly command

        :param commandIdentifier: the command name
        :param arguments: list of all arguments
        """
        return (commandIdentifier + json.dumps(arguments)).encode(ENCODING)

    @staticmethod
    def decode(data: Union[bytes, str]) -> Tuple[str, list]:
        """
        from a formatted request return a more human-readable request

        :param data: the formatted data
        """
        if isinstance(data, bytes):
            data = data.decode(ENCODING)
        separatorIndex = data.find("[")
        commandIdentifier = data[:separatorIndex]
        arguments = json.loads(data[separatorIndex:])
        return (commandIdentifier, arguments)

def sendAll(connection, data: Union[bytes, str]):
    """
    sends all data, this is not the default socket.sendall() function

    :param connection: the socket where to send the data
    :param data: the data to send
    """

    if isinstance(data, str):
        data = data.encode(ENCODING)

    data = len(data).to_bytes(HEADER_LENGTH, byteorder=HEADER_BYTEORDER) + data
    while data:
        sent = connection.send(data)
        data = data[sent:]

def receiveAll(connection) -> Union[str, None]:
    """
    recieves all data from a connection

    :param connection: the socket where recieve data
    """

    head = connection.recv(HEADER_LENGTH) #read the header from a buffered request

    if head:
        byteCount = int.from_bytes(head, byteorder=HEADER_BYTEORDER)
        data = connection.recv(byteCount) #read the actual message of len head

        while len(data) < byteCount:
            data += connection.recv(byteCount - len(data))

        return data
    return None
