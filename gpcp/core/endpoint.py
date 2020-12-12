from gpcp.utils.errors import ConfigurationError
from gpcp.utils.base_types import getFromId
from gpcp.core import packet
from typing import Union
import logging
import socket
import json

logger = logging.getLogger(__name__)

class EndPoint():

    def __init__(self, socket, handler, server, role):
        self.socket  = socket
        self.handler = handler
        self.server  = server
        self.localAddress  = self.socket.getsockname()
        self.remoteAddress = self.socket.getpeername()

        # setting up initial data to send
        config = json.dumps({
            "role":role
        })

        # initial data transfer
        packet.sendAll(self.socket, config)
        remoteConfig = json.loads(packet.receiveAll(self.socket))
        logger.debug(f"remote config sent to {self.remoteAddress}: {config}")
        logger.debug(f"remote config recieved on {self.localAddress}: {remoteConfig}")

        # checking config validity
        if remoteConfig["role"] not in ["R", "A", "AR", "RA"]:
            logger.error(f"invalid configuration argument '{remoteConfig['role']}' for 'role' in connection {self.remoteAddress}, closing")
            self.socket.close()

        # checking if the endpoints can actually talk to each other
        if remoteConfig["role"] == "R" and role == "R":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only respond, closing")
            self.socket.close()
        elif remoteConfig["role"] == "A" and role == "A":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only request, closing")
            self.socket.close()
        
        # locking the handler if needed
        if role == "A":
            self.handler._LOCK = True
        else:
            self.handler._LOCK = False

    def mainLoop(self):
        while True:
            try:
                data = packet.receiveAll(self.socket)
                if data is None: # connection was closed
                    logger.info(f"received None data from {self.remoteAddress}, closing connection")
                    # self.socket._closed is True only if self.socket.close() is called
                    if self.socket._closed == False:
                        self.closeConnection()
                    break
                else: # send the handler response to the client
                    logger.debug(f"received data from {self.remoteAddress}")
                    response = self.handler.handleData(data)
                    if response == "ENDPOINT NOT STARTED TO THIS SCOPE":
                        logger.warning(f"unexpected request with data={data} while handler locked from {self.remoteAddress}")
                    packet.sendAll(self.socket, response)
            except BlockingIOError:
                pass

    def closeConnection(self, mode: str = "rw"):
        """
        Closes the connection to the other end point

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
        namespace is the same as the main class.

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

    def raw_request(self, data: Union[bytes, str]):
        """
        send a formatted request to the server and return the response

        :param data: the formatted request to send
        """
        logger.debug(f"raw_request() called with data={data}")
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
        result = json.loads(self.raw_request(data).decode(packet.ENCODING))
        logger.debug(f"commandRequest() received result={result}")
        return result
