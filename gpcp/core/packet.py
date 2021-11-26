"""packet module containing functions to handle packets"""
from typing import Union, Tuple
import logging
import json
import socket

logger = logging.getLogger(__name__)

# header encoding data
HEADER_BYTEORDER = "big"
HEADER_LENGTH    = 4
ENCODING         = "utf-8"

# header packet type numbers
# numbers available: from 0 to 15
KEEP_ALIVE   = 0  # 0b0000 | 0x0
STD_REQUEST  = 1  # 0b0001 | 0x1
STD_RESPONSE = 2  # 0b0010 | 0x2
STD_PUSH     = 3  # 0b0011 | 0x3
STD_ERROR    = 15 # 0b1111 | 0xf

# list containing all packet types except for KEEP_ALIVE
PACKET_TYPES = [STD_REQUEST, STD_RESPONSE, STD_PUSH, STD_ERROR]

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
    def encode(length: int, packetType: int) -> bytes:
        # 0x0fffffff == 0000 1111|1111 1111|1111 1111|1111 1111
        # header bits-> ^^^^
        if length > 0x0fffffff or length < 0:
            raise ValueError("length too " + "small" if length < 0 else "large" + " to handle")

        if packetType in PACKET_TYPES:
            byteList = [
                packetType << 4 + ((length >> 24) & 0x0f),
                (length >> 16) & 0xff,
                (length >> 8)  & 0xff,
                (length)       & 0xff
            ]
        elif packetType == KEEP_ALIVE:
            logger.warning(f"tried to encode packet header with packetType KEEP_ALIVE, please use packet.sendKeepAlive function")
            return 0
        else:
            raise ValueError(f"packet type {packetType} not recognized")

        logger.debug(f"header encoded from length {length}, packetType {packetType} to: {bytes(byteList)}")
        return byteList

    @staticmethod
    def decode(head) -> int:
        # 0xf0 = 1111 0000
        packetType = (head[0] & 0xf0) >> 4

        if packetType == 0:
            logger.debug(f"header decoded, recieved KEEP_ALIVE")
            return (0, 0)

        # 0x0f = 0000 1111
        byteList = [head[0] & 0x0f]
        for i in range(1, HEADER_LENGTH):
            byteList.append(head[i] & 0xff)

        logger.debug(f"header decoded with length {length}, packetType {packetType} from: {bytes(byteList)}")
        return (
            int.from_bytes(bytes(byteList), HEADER_BYTEORDER),
            packetType
        )

def sendKeepAlive(connection):
    logger.debug(f"sent KEEP_ALIVE")
    connection.send(0)

def sendAll(connection, data: Union[bytes, str], packetType: int = STD_RESPONSE):
    """
    sends all data, this is not the default socket.sendall() function

    :param connection: the socket where to send the data
    :param data: the data to send
    :param packetType: the packet type
    """

    if isinstance(data, str):
        data = data.encode(ENCODING)

    data = bytes(Header.encode(len(data), packetType)) + data
    while data:
        logger.debug(f"sending data fragment {data} to {connection.getpeername()}")
        sent = connection.send(data)
        data = data[sent:]

def receiveAll(connection) -> Union[str, None]:
    """
    recieves all data from a connection

    :param connection: the socket where recieve data
    """

    try:
        #read the first byte of the header from a buffered request
        head = connection.recv(1)

        if head is None: # recieve None if connection is closed
            return (None, None)
        elif head != 0: # recieve something if there is packet
            head += connection.recv(3)
            byteCount, packetType = Header.decode(head)
            data = connection.recv(byteCount) #read the actual message of len head
            logger.debug(f"receiving data fragment {data} from {connection.getpeername()}")

            while len(data) < byteCount:
                fragment = connection.recv(byteCount - len(data))
                logger.debug(f"receiving data fragment {fragment} from {connection.getpeername()}")
                data += fragment

            return (data, packetType)
        else: # KEEP_ALIVE
            return (None, 0)
    except socket.timeout:
        raise TimeoutError()
