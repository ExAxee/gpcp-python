import json
from typing import Callable, Union
from gpcp.utils import packet
from gpcp.utils.filters import command, unknownCommand, FunctionType
from gpcp.utils.base_types import toId, JsonObject

import logging
logger = logging.getLogger(__name__)

class BaseHandler:

    # to be overridden
    def onConnected(self, server, connection, address):
        """
        To be overridden, can be used to prepare the handler.

        :param server: the gpcp server that established the connection
        :param connection: the just opened socket connection
        :param address: the address of the just opened connection
        """
        logger.debug(f"base onConnected called with address={address}")

    def onDisonnected(self, server, connection, address) -> Union[bytes, None]:
        """
        To be overridden, can be used to send a last message to the client
        and to clean up the handler.

        :param server: the gpcp server that established the connection
        :param connection: the socket connection being closed
        :param address: the address of the connection being closed
        :returns: a message or None
        """
        logger.debug(f"base onDisonnected called with address={address}")

    @classmethod
    def loadHandlers(cls):
        """
        loads all handlers in a BaseHandler derivated object
        """

        logger.debug(f"loadHandlers called on class " + cls.__name__)
        if hasattr(cls, "commandFunctions") and isinstance(cls.commandFunctions, dict):
            logger.warning(f"commands already loaded for class " + cls.__name__)
            return
        cls.commandFunctions = {}
        cls.unknownCommandFunction = None

        #get all function with a __gpcp_metadata__ value
        functionMapRaw = [func for func in [getattr(cls, func) for func in dir(cls)]
                          if callable(func) and hasattr(func, "__gpcp_metadata__")]

        for func in functionMapRaw:
            # func.__gpcp_metadata__ = (<functionType>, ...)
            functionType = func.__gpcp_metadata__[0]

            if functionType == FunctionType.command:
                # func.__gpcp_metadata__ = (command, <command trigger>, <description>, <return type>
                #   [(<param 1 type>, <param 1 name>), (<param 2 type>, <param 2 name>), ...])
                commandTrigger, description, returnType, arguments = func.__gpcp_metadata__[1:]

                if commandTrigger in cls.commandFunctions:
                    raise ValueError(f"command {commandTrigger} already registered and"
                                     + f" mapped to {cls.commandFunctions[commandTrigger]}")
                cls.commandFunctions[commandTrigger] = (func, description, returnType, arguments)

            elif functionType == FunctionType.unknown:
                # func.__gpcp_metadata__ = (unknown,)
                if cls.unknownCommandFunction is not None:
                    raise ValueError(f"handler for unknown commands already registered"
                                     + f" and mapped to {cls.unknownCommandFunction}")
                cls.unknownCommandFunction = func

            else:
                raise ValueError(f"invalid __gpcp_metadata__ for function"
                                 + f" {func.__name__}: {func.__gpcp_metadata__}")

        logger.info(f"found {'no' if cls.unknownCommandFunction is None else 'a'} unknownCommandFunction"
                    + f" and {len(cls.commandFunctions)} commandFunctions "
                    + str([f[0].__name__ for f in cls.commandFunctions.values()]))

    def handleData(self, data: Union[bytes, str]):
        """
        calls the corrispondent handler function from a given request
        """

        logger.debug(f"handleData called on {self.__class__.__name__} with data={data}")
        commandIdentifier, arguments = packet.CommandData.decode(data)
        logger.debug(f"commandIdentifier={commandIdentifier} and arguments={arguments}")

        try:
            function, _, returnType, argumentTypes = self.commandFunctions[commandIdentifier]
        except KeyError:
            logger.info(f"unknown command {commandIdentifier}")
            if self.unknownCommandFunction is None:
                logger.warning(f"missing unknownCommandFunction when handling {commandIdentifier}: returning \"\"")
                return b""
            return self.unknownCommandFunction(commandIdentifier, arguments)

        # convert parameters from `bytes` to the types of `function` arguments
        convertedArguments = []
        for i, argument in enumerate(arguments):
            argType, _ = argumentTypes[i]
            convertedArguments.append(argType.deserialize(argument))

        # convert the return value to `bytes` from the specified type
        returnValue = function(self, *convertedArguments)
        logger.debug(f"return value for command {commandIdentifier}: {returnValue}")
        return json.dumps(returnType.serialize(returnValue))

    @command
    def requestCommands(self) -> JsonObject:
        """
        requests the commands list from the server and returns it
        """

        logger.debug(f"requestCommands called")

        serializedCommands = []
        for commandTrigger, metadata in self.commandFunctions.items():
            _, description, returnType, arguments = metadata

            serializedCommands.append({
                "name": commandTrigger,
                "arguments": [{"name": argName, "type": toId(argType)}
                              for argType, argName in arguments],
                "return_type": toId(returnType),
                "description": description,
            })

        return serializedCommands

def buildHandlerFromFunction(func: Callable) -> type:
    class WrapperHandler(BaseHandler):
        @unknownCommand
        def wrapper(self, commandIdentifier, arguments):
            return json.dumps(func(self, commandIdentifier, arguments))

    WrapperHandler.loadHandlers()
    return WrapperHandler
