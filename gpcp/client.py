import socket
import json
from gpcp.utils.base_types import getFromId
from gpcp.utils import packet

class Client:

    def __init__(self):
        """
        If the callable default_handler is specified all
        responses to all requests will be handled by it
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.closeConnection()

    def connect(self, host: str, port: int):
        """
        Connect to a server

        :param host: the host server ip or address
        :param port: the port on the host server
        :returns: self, so that this function can be called inside a `with`
        """

        if not isinstance(host, str):
            raise ValueError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")

        self.socket.connect((host, port))
        return self

    def closeConnection(self, mode: str="rw"):
        """
        Closes the connection to the server
        :param mode: r = read, w = write, rw = read and write
        """

        if mode == "rw":
            self.socket.shutdown(socket.SHUT_RDWR)
        elif mode == "r":
            self.socket.shutdown(socket.SHUT_RD)
        elif mode == "w":
            self.socket.shutdown(socket.SHUT_WR)
        else:
            raise ValueError("close mode must be 'r' or 'w' or 'rw'")

        self.socket.close()


    def loadInterface(self, raw_interface: list, namespace: type):
        """
        Given a raw interface string or dict it will load the remote interface and make it
        available to the user with Client.RemoteCall.<command>(*args, **kwargs)

        this is the definition of a remote command:
        {
            name: str,
            arguments: [{name: str, type: type}, ...],
            return_type: type,
            doc: str
        }

        raw_interface can have multiple commands in a array, like so:

        raw_interface = [command_1, command_2, command_3, etc]

        every command MUST follow the above definition
        """

        if isinstance(raw_interface, bytes) or isinstance(raw_interface, str):
            raw_interface = json.loads(raw_interface)
        else:
            pass

        for command in raw_interface:
            def generateWrapperFunction():
                def wrapper(*args):
                    arguments = []
                    for i in range(len(args)):
                        arguments.append(wrapper.argumentTypes[i].serialize(args[i]))
                    returnedData = self.commandRequest(wrapper.commandIdentifier, arguments)
                    return wrapper.returnType.deserialize(returnedData)
                return wrapper

            wrapper = generateWrapperFunction()

            wrapper.commandIdentifier = command["name"]
            wrapper.argumentTypes = [getFromId(arg["type"]) for arg in command["arguments"]]
            wrapper.returnType = getFromId(command["return_type"])
            wrapper.__doc__ = command["description"]

            setattr(namespace, command["name"], wrapper)

    def request(self, request):
        packet.sendAll(self.socket, request)
        return packet.receiveAll(self.socket)

    def commandRequest(self, commandIdentifier, arguments):
        data = packet.CommandData.encode(commandIdentifier, arguments)
        return self.request(data).decode(packet.ENCODING)
