from .base_types import Integer, HexInteger, String, Bytes, Float, Array, Json
from .utils import ENCODING
import enum

class BaseHandler:

    defaultFunctionMap = {"command":{}, "object": None, "file": None, "unknown": None}

    class function_types(enum.Enum):
        command = 0
        object  = 1
        file    = 2
        unknown = 3

    def __init__(self):
        pass

    def load_handlers(self):
        """loads all handlers in a BaseHandler derivated object"""

        #get all function with a __gpcp_metadata__ value
        functionMapRaw = [func for func in dir(self) if callable(getattr(self, func)) and hasattr(func, "__gpcp_metadata__")]

        self.functionMap = BaseHandler.defaultFunctionMap.copy() #copy the default function mapping
        for func in functionMapRaw:

            if func.__gpcp_metadata__[0] == BaseHandler.function_types.command: #func.__gpcp_metadata__ = ("command", <command trigger>)
                if func.__gpcp_metadata__[1] not in self.functionMap["command"].keys():
                    self.functionMap["command"][func.__gpcp_metadata__[1]] = func
                else:
                    raise ValueError(f"command {func.__gpcp_metadata__[1]} already registered and mapped to {self.functionMap['command'][func.__gpcp_metadata__[1]]}")

            elif func.__gpcp_metadata__[0] == BaseHandler.function_types.object: #func.__gpcp_metadata__ = ("object")
                if self.functionMap["object"] is None:
                    self.functionMap["object"] = func
                else:
                    raise ValueError(f"object handler already registered and mapped to {self.functionMap['object']}")

            elif func.__gpcp_metadata__[0] == BaseHandler.function_types.file: #func.__gpcp_metadata__ = ("file")
                if self.functionMap["file"] is None:
                    self.functionMap["file"] = func
                else:
                    raise ValueError(f"file handler already registered and mapped to {self.functionMap['file']}")

            elif func.__gpcp_metadata__[0] == BaseHandler.function_types.unknown: #func.__gpcp_metadata__ = ("unknown")
                if self.functionMap["unknown"] is None:
                    self.functionMap["unknown"] = func
                else:
                    raise ValueError(f"unknown handler already registered and mapped to {self.functionMap['unknown']}")

            else:
                raise ValueError(f"error in __gpcp_metadata__'s value of {func}: {__gpcp_metadata__}")

    def handleCommand(self, command):
        parts = command.split(b" ")
        parts = list(filter(None, parts)) # remove empty
        functionIdentifier = parts[0].decode(ENCODING)

        try:
            function = self.functionMap[functionIdentifier]
        except KeyError:
            if self.unknownCommandFunction:
                self.unknownCommandFunction(functionIdentifier, parts[1:])
            else:
                pass # TODO some other type of error handling
            return

        arguments = []
        for i in range(len(parts) - 1):
            arguments.append(function[1][i].fromString(parts[i+1]))
        function[0](functionIdentifier, *arguments)

if __name__ == "__main__":
    bh = BaseHandler()
    bh.handleCommand(b'hello     {"a":true,"b":["1","2","3"],"c":{"d":5,"e":null}}   0x10 ciao! ciaone 17.19 [5,17,28]')
