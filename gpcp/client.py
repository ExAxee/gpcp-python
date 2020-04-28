import socket
from gpcp.utils import packet

class Client:

    @staticmethod
    def __defaultRemoteCallMethod__():
        print()

    def __init__(self, default_handler=None):
        """
        If the callable default_handler is specified all
        responses to all requests will be handled by it
        """

        if default_handler is not None:
            if not callable(default_handler):
                raise ValueError(
                    f"invalid option '{default_handler}' for default_handler, must be callable")
        self.default_handler = default_handler

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        return self

    def loadInterface(self, raw_interface):
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

        interface = {}
        callArgs = {}

        for command in raw_interface:
            callFunc = Client.__defaultRemoteCallMethod__
            callFunc.__doc__ = command.doc
            callFunc.__name__ = command.name

            for argument in command.arguments:
                callArgs[argument.name] = argument.type

            callArgs["return"] = argument.return_type
            callFunc.__annotations__ = callArgs

            interface[command.name] = callFunc

        self.RemoteCall = type('RemoteCall', (object,), interface) #generate the class object

    def connect(self, host, port):
        """connect to a server"""

        if not isinstance(host, str):
            raise ValueError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ValueError(f"invalid option '{port}' for port, must be integer")

        self.socket.connect((host, port))

    def request(self, request, handler=None):
        """if handler is specified it will overwrite temporairly the default_handler"""

        if handler is not None and not callable(handler):
            raise ValueError(f"invalid option '{handler}' for handler, must be callable")

        packet.sendAll(self.socket, request)

        data = packet.receiveAll(self.socket)
        if data is not None:
            if handler is not None:
                handler(self.socket, data)
            elif self.default_handler is not None:
                self.default_handler(self.socket, data)
        return data

    def closeConnection(self, mode="RW"):
        """closes the connection to the server, RW = read and write, R = read, W = write"""
        if mode == "RW":
            self.socket.shutdown(socket.SHUT_RDWR)
        elif mode == "R":
            self.socket.shutdown(socket.SHUT_RD)
        elif mode == "W":
            self.socket.shutdown(socket.SHUT_WR)
        else:
            raise ValueError("close mode must be 'R' or 'W' or 'RW'")

        self.socket.close()

    def __exit__(self, exc_type, exc_value, exc_tb):

        self.closeConnection()
        if exc_type and exc_value and exc_tb is not None:
            print(exc_type, "\n", exc_value, "\n", exc_tb)
