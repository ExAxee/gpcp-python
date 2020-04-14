from json import loads
from .utils import ENCODING


class TypeBase:
    @staticmethod
    def fromString(string):
        raise NotImplementedError()

    @staticmethod
    def getIfBuiltIn(argumentType):
        """
        If needed converts built-in types into the corresponding TypeBase
            :param argumentType: a type to convert if it's a built-in one
        """

        if argumentType == bytes:
            return Bytes
        if argumentType == str:
            return String
        if argumentType == int:
            return Integer
        if argumentType == float:
            return Float
        return argumentType


class Bytes(TypeBase):
    @staticmethod
    def fromString(string):
        return string


class String(TypeBase):
    @staticmethod
    def fromString(string):
        return string.decode(ENCODING)


class Integer(TypeBase):
    @staticmethod
    def fromString(string):
        return int(string.decode(ENCODING), base=10)


class HexInteger(TypeBase):
    @staticmethod
    def fromString(string):
        return int(string.decode(ENCODING), base=16)


class Float(TypeBase):
    @staticmethod
    def fromString(string):
        return float(string.decode(ENCODING))


class Json(TypeBase):
    @staticmethod
    def fromString(string):
        return loads(string.decode(ENCODING))


class Array(TypeBase):
    def __init__(self, elementType):
        self.elementType = TypeBase.getIfBuiltIn(elementType)

    def fromString(self, string):
        if string[0] != ord("[") or string[-1] != ord("]"):
            raise ValueError("Not an array: " + string.decode(ENCODING))

        parts = string[1:-1].split(b",")
        return [self.elementType.fromString(part) for part in parts]
