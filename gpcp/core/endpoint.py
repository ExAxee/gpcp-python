from threading import Event, Thread
from typing import Union
import logging
import json
from gpcp.utils.base_types import getFromId
from gpcp.utils.errors import ConfigurationError
from gpcp.core.dispatcher import Dispatcher
from gpcp.core import packet

logger = logging.getLogger(__name__)

class EndPoint():

    def __init__(self, socket, validatedRole: str, handlerInstance):
        self._stop = False
        self._finishedInitializing = False
        self.socket = socket
        self.localAddress = self.socket.getsockname()
        self.remoteAddress = self.socket.getpeername()
        self.role = validatedRole
        self.handler = handlerInstance

        # setting up initial data to send
        config = json.dumps({
            "role": self.role
        })

        # initial data transfer
        packet.sendAll(self.socket, config)
        logger.debug(f"remote config sent to {self.remoteAddress}: {config}")
        remoteConfig = json.loads(packet.receiveAll(self.socket)[0])
        logger.debug(f"remote config recieved on {self.localAddress}: {remoteConfig}")

        # checking config validity
        if remoteConfig["role"] not in ["R", "A", "AR", "RA"]:
            logger.error(f"invalid configuration argument '{remoteConfig['role']}' for 'role' in connection {self.remoteAddress}, closing")
            self.socket.close()

        # checking if the endpoints can actually talk to each other
        if remoteConfig["role"] == "R" and self.role == "R":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only respond, closing")
            self.socket.close()
        elif remoteConfig["role"] == "A" and self.role == "A":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only request, closing")
            self.socket.close()

        # locking the handler if needed
        if self.handler is not None:
            if self.role == "A":
                self.handler._LOCK = True
            else:
                self.handler._LOCK = False

        self.startMainLoopThread()
        while not self._finishedInitializing:
            pass # wait for the main loop thread to start

    def mainLoop(self):
        #dispatcher thread setup
        self.dispatcher = Dispatcher(self.socket)
        self._finishedInitializing = True

        while not self._stop:
            #wait for a request to come
            try:
                data = self.dispatcher.request.waitForUpdate()
            except TimeoutError:
                continue

            if data is None: # connection was closed
                logger.info(f"received None data from {self.remoteAddress}, closing connection")
                self._closeConnection(True)
                break

            else: # send the handler response to the client
                logger.debug(f"received data from {self.remoteAddress}")
                response = self.handler.handleData(data)
                if response == "ENDPOINT NOT STARTED TO THIS SCOPE":
                    logger.warning(f"unexpected request with data={data} while handler locked from {self.remoteAddress}")
                packet.sendAll(self.socket, response)

    def startMainLoopThread(self):
        self.mainLoopThread = Thread(target=self.mainLoop)
        self.mainLoopThread.setName(f"connection ({self.remoteAddress[0]}:{self.remoteAddress[1]})")
        self.mainLoopThread.start()

    def _closeConnection(self, calledFromMainLoopThread: bool):
        """
        Closes the connection to the other end point

        :param mode: r = read, w = write, rw = read and write (default: 'rw')
        """

        logger.info(f"_closeConnection() called with calledFromMainLoopThread={calledFromMainLoopThread}")

        if self.isStopped():
            logger.info(f"_closeConnection() ignored since endpoint already stopped")
        else:
            # set stop flags for threads: dispatcher.setStopFlag() also sets events for request/response buffers
            self._stop = True
            if self._finishedInitializing:
                self.dispatcher.setStopFlag()

            if not calledFromMainLoopThread:
                # first join our thread, which should be instant since events for request/response buffers were set
                self.mainLoopThread.join()
            if self._finishedInitializing:
                # then join the dispatcher (could take up to the timeout passed at the beginning)
                self.dispatcher.thread.join()

            # close the socket
            if not self.socket._closed:
                self.socket.close()

    def closeConnection(self):
        self._closeConnection(False)

    def isStopped(self):
        return self.socket._closed and not self.mainLoopThread.is_alive()

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
            #request the raw interface if not provided
            rawInterface = self.commandRequest("requestCommands", [])

        if isinstance(rawInterface, (bytes, str)):
            rawInterface = json.loads(rawInterface)

        for command in rawInterface:
            def generateWrapperFunction():
                #declaring handler method
                def wrapper(*args):
                    arguments = []
                    for i, arg in enumerate(args):
                        arguments.append(wrapper.argumentTypes[i].serialize(arg))
                    returnedData = self.commandRequest(wrapper.commandIdentifier, arguments)
                    return wrapper.returnType.deserialize(returnedData)
                return wrapper

            wrapper = generateWrapperFunction()

            #setting up handler method data
            wrapper.commandIdentifier = command["name"]
            wrapper.argumentTypes = [getFromId(arg["type"]) for arg in command["arguments"]]
            wrapper.returnType = getFromId(command["return_type"])
            wrapper.__doc__ = command["description"]

            logger.debug(f"loaded command with commandIdentifier={wrapper.commandIdentifier}, description=\"{wrapper.__doc__}\""
                         + f", argumentTypes={wrapper.argumentTypes}, returnType={wrapper.returnType}")
            #assigning the method to the namespace class
            setattr(namespace, command["name"], wrapper)

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
        #format the command into a valid request
        data = packet.CommandData.encode(commandIdentifier, arguments)
        #send the request
        packet.sendAll(self.socket, data, isRequest=True)
        #wait for the response trigger to activate and load the response
        response = self.dispatcher.response.waitForUpdate()
        result = json.loads(response.decode(packet.ENCODING))
        logger.debug(f"commandRequest() received result={result}")
        return result
