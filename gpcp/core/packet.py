"""packet module containing functions to handle packets"""
from typing import Union, Tuple
from threading import current_thread
import logging
import json
import socket

logger = logging.getLogger(__name__)

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
        logger.debug(f"decoded command from '{data}' -> args: '{arguments}'; cmd: '{commandIdentifier}'")
        return (commandIdentifier, arguments)

class Header:

    @staticmethod
    def encode(length: int, isRequest: bool) -> bytes:
        if length > 0x7fffffff: #0x7fffffff == 01111111 11111111 11111111 11111111
            raise ValueError("length too big to handle")

        byteList = [isRequest << 7 + ((length >> 24) & 0x7f), (length >> 16) & 0xff, (length >> 8) & 0xff, (length) & 0xff]
        logger.debug(f"header encoded from length {length}, isRequest {isRequest} to: {bytes(byteList)}")
        return byteList

    @staticmethod
    def decode(head) -> int:
        isRequest = bool(head[0] & 0x80)

        byteList = [head[0] & 0x7f]
        for i in range(1, HEADER_LENGTH):
            byteList.append(head[i] & 0xff)

        logger.debug(f"header decoded from head {head} to: isRequest {isRequest}; bytes {byteList}")
        return (int.from_bytes(bytes(byteList), HEADER_BYTEORDER), isRequest)

def sendAll(connection, data: Union[bytes, str], isRequest: bool = False):
    """
    sends all data, this is not the default socket.sendall() function

    :param connection: the socket where to send the data
    :param data: the data to send
    """

    if isinstance(data, str):
        data = data.encode(ENCODING)

    data = bytes(Header.encode(len(data), isRequest)) + data
    while data:
        logger.debug(f"sending data fragment {data} to {current_thread().name}")
        sent = connection.send(data)
        data = data[sent:]

def receiveAll(connection) -> Union[str, None]:
    """
    recieves all data from a connection

    :param connection: the socket where recieve data
    """

    try:
        head = connection.recv(HEADER_LENGTH) #read the header from a buffered request

        if head:
            byteCount, isRequest = Header.decode(head)
            data = connection.recv(byteCount) #read the actual message of len head
            logger.debug(f"receiving data fragment {data} from {current_thread().name}")

            while len(data) < byteCount:
                fragment = connection.recv(byteCount - len(data))
                logger.debug(f"receiving data fragment {fragment} from {current_thread().name}")
                data += fragment

            return (data, isRequest)
        return (None, None)
    except socket.timeout:
        raise TimeoutError()
