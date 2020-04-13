from base_types import Integer, HexInteger, String, Bytes, Float, Array, Json
from utils import ENCODING

class BaseHandler:
    def __init__(self):
        # TODO use decorators to create function map at runtime
        self.functionMap = {
            "hello": (print, [Json, HexInteger, String, Bytes, Float, Array(Integer)])
        }
        self.unknownCommandFunction = print

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