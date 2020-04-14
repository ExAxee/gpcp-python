from .base_types import Integer, HexInteger, String, Bytes, Float, Array, Json
from .utils import ENCODING
import enum

class BaseHandler:


    class FunctionType(enum.Enum):
        command = 0
        unknown = 1

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

            if func.__gpcp_metadata__[0] == cls.FunctionType.command: #func.__gpcp_metadata__ = ("command", <command trigger>)
                if func.__gpcp_metadata__[1] not in cls.commandFunctions.keys():
                    cls.commandFunctions[func.__gpcp_metadata__[1]] = func
                else:
                    raise ValueError(f"command {func.__gpcp_metadata__[1]} already registered and mapped to {cls.commandFunctions[func.__gpcp_metadata__[1]]}")

            elif func.__gpcp_metadata__[0] == cls.FunctionType.unknown: #func.__gpcp_metadata__ = ("unknown")
                if cls.unknownCommandFunction is None:
                    cls.unknownCommandFunction = func
                else:
                    raise ValueError(f"unknown handler already registered and mapped to {cls.unknownCommandFunction}")

            else:
                raise ValueError(f"error in __gpcp_metadata__'s value of {func}: {func.__gpcp_metadata__}")

    def handleCommand(self, command):
        parts = command.split(b" ")
        parts = list(filter(None, parts)) # remove empty
        functionIdentifier = parts[0].decode(ENCODING)

        try:
            function = self.commandFunctions[functionIdentifier]
        except KeyError:
            if self.unknownCommandFunction is not None:
                return self.unknownCommandFunction(functionIdentifier, parts[1:])
            else:
                return b"Unknown command" # TODO some other type of error handling

        arguments = []
        #for i in range(len(parts) - 1):
        #    arguments.append(function[1][i].fromString(parts[i+1]))
        #function[0](functionIdentifier, *arguments)
        return function(self, functionIdentifier, *parts[1:])

if __name__ == "__main__":
    bh = BaseHandler()
    bh.handleCommand(b'hello     {"a":true,"b":["1","2","3"],"c":{"d":5,"e":null}}   0x10 ciao! ciaone 17.19 [5,17,28]')
