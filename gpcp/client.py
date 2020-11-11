import socket
import json
from typing import Union
from gpcp.core import packet
from gpcp.utils.base_types import getFromId
from gpcp.utils.errors import ConfigurationError

import logging
logger = logging.getLogger(__name__)

class Client:
    """
    gpcp client main class, used for creating and using a client
    """

    def connect(self, host: str, port: int):
        """
        Connect to a server

        :param host: the host server ip or address
        :param port: the port on the host server
        :returns: self, so that this function can be called inside a `with`
        """

        logger.info(f"connect() called with host={host}, port={port}")

        if not isinstance(host, str):
            raise ConfigurationError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ConfigurationError(f"invalid option '{port}' for port, must be integer")

        self.socket.connect((host, port))
        return self

    def closeConnection(self, mode: str = "rw"):
        """
        Closes the connection to the server

        :param mode: r = read, w = write, rw = read and write (default: 'rw')
        """

        logger.info(f"closeConnection() called with mode={mode}")

        if mode == "rw":
            self.socket.shutdown(socket.SHUT_RDWR)
        elif mode == "r":
            self.socket.shutdown(socket.SHUT_RD)
        elif mode == "w":
            self.socket.shutdown(socket.SHUT_WR)
        else:
            raise ConfigurationError(f"invalid option '{mode}' for mode, must be 'r' or 'w' or 'rw'")

        self.socket.close()

    def loadInterface(self, namespace: type, rawInterface: list = None):
        """
        Retrieve and load the remote interface and make it available to
        the user with `<namespace>.<command>(*args, **kwargs)`, usually
        namespace is the same as the Client class.

        this is the definition of a remote command:
        {
            name: str,
            arguments: [{name: str, type: type}, ...],
            return_type: type,
            doc: str
        }

        rawInterface can have multiple commands in a array, like so:
        rawInterface = [command_1, command_2, command_3, etc]

        every command MUST follow the above definition

        :param namespace: the object where the commands will be loaded
        :param rawInterface: raw interface string or dict to load. If None the interface
            will be loaded from the server by calling the command `requestCommands()`
        """

        logger.debug(f"loadInterface() called with namespace={namespace}, rawInterface={rawInterface}")

        if rawInterface is None:
            rawInterface = self.commandRequest("requestCommands", [])

        if isinstance(rawInterface, (bytes, str)):
            rawInterface = json.loads(rawInterface)

        for command in rawInterface:
            def generateWrapperFunction():
                def wrapper(*args):
                    arguments = []
                    for i, arg in enumerate(args):
                        arguments.append(wrapper.argumentTypes[i].serialize(arg))
                    returnedData = self.commandRequest(wrapper.commandIdentifier, arguments)
                    return wrapper.returnType.deserialize(returnedData)
                return wrapper

            wrapper = generateWrapperFunction()

            wrapper.commandIdentifier = command["name"]
            wrapper.argumentTypes = [getFromId(arg["type"]) for arg in command["arguments"]]
            wrapper.returnType = getFromId(command["return_type"])
            wrapper.__doc__ = command["description"]

            logger.debug(f"loaded command with commandIdentifier={wrapper.commandIdentifier}, description=\"{wrapper.__doc__}\""
                         + f", argumentTypes={wrapper.argumentTypes}, returnType={wrapper.returnType}")
            setattr(namespace, command["name"], wrapper)

    def request(self, data: Union[bytes, str]):
        """
        send a formatted request to the server and return the response

        :param data: the formatted request to send
        """
        logger.debug(f"request() called with data={data}")
        packet.sendAll(self.socket, data)
        return packet.receiveAll(self.socket)

    def commandRequest(self, commandIdentifier: str, arguments: list) -> str:
        """
        Format a command request with given arguments, send it and return the response.
        Remember to deserialize the response using one of the types in
        `gpcp.utils.base_types` or one extending them, otherwise the response will not
        make sense since it was serialized on the server's end.

        :param arguments: list of all arguments to send to the server
        :param commandIdentifier: the name of the command to call
        """
        logger.debug(f"commandRequest() called with commandIdentifier={commandIdentifier}, arguments={arguments}")
        data = packet.CommandData.encode(commandIdentifier, arguments)
        result = json.loads(self.request(data).decode(packet.ENCODING))
        logger.debug(f"commandRequest() received result={result}")
        return result

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.closeConnection()
