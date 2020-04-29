import json
from gpcp.utils import packet
from gpcp.utils.filters import command, FunctionType
from gpcp.utils.base_types import toId, Json

class BaseHandler:

    def __init__(self):
        pass

    @classmethod
    def loadHandlers(cls):
        """loads all handlers in a BaseHandler derivated object"""

        if hasattr(cls, "commandFunctions") and isinstance(cls.commandFunctions, dict):
            return # already loaded
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
                                 + f" {func}: {func.__gpcp_metadata__}")

    def handleData(self, data):
        commandIdentifier, arguments = packet.dataToCommand(data)

        try:
            function, _, returnType, argumentTypes = self.commandFunctions[commandIdentifier]
        except KeyError:
            if self.unknownCommandFunction is None:
                return b"Unknown command" # TODO some other type of error handling
            return self.unknownCommandFunction(commandIdentifier, arguments)

        # convert parameters from `bytes` to the types of `function` arguments
        convertedArguments = []
        for i in range(len(arguments)):
            argType, _ = argumentTypes[i]
            convertedArguments.append(argType.deserialize(arguments[i]))

        # convert the return value to `bytes` from the specified type
        returnValue = function(self, commandIdentifier, *convertedArguments)
        return json.dumps(returnType.serialize(returnValue))

    @command
    def requestCommands(self, _) -> Json:
        """requests the commands list from the server and returns it."""

        serializedCommands = []
        for commandTrigger, metadata in self.commandFunctions.items():
            _, description, returnType, arguments = metadata

            serializedCommands.append({
                "arguments": [{"name": argName, "type": toId(argType)}
                              for argType, argName in arguments],
                "return_type": toId(returnType),
                "name": commandTrigger,
                "description": description,
            })

        return serializedCommands
