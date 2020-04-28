import json


class TypeBase:
    # method to override
    @staticmethod
    def fromBytes(string):
        raise NotImplementedError()

    # method to override
    @staticmethod
    def toBytes(value):
        return NotImplementedError()

    # utility method (NOT to override)
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
    def fromBytes(string):
        return string

    @staticmethod
    def toBytes(value):
        return str(value).encode(ENCODING)


class String(TypeBase):
    @staticmethod
    def fromBytes(string):
        return string.decode(ENCODING)

    @staticmethod
    def toBytes(value):
        return value.encode(ENCODING)


class Integer(TypeBase):
    @staticmethod
    def fromBytes(string):
        return int(string.decode(ENCODING), base=10)

    @staticmethod
    def toBytes(value):
        return str(value).encode(ENCODING)


class HexInteger(TypeBase):
    @staticmethod
    def fromBytes(string):
        return int(string.decode(ENCODING), base=16)

    @staticmethod
    def toBytes(value):
        return hex(value).encode(ENCODING)


class Float(TypeBase):
    @staticmethod
    def fromBytes(string):
        return float(string.decode(ENCODING))

    @staticmethod
    def toBytes(value):
        return str(value).encode(ENCODING)


class Json(TypeBase):
    @staticmethod
    def fromBytes(string):
        return json.loads(string.decode(ENCODING))

    @staticmethod
    def toBytes(value):
        return json.dumps(value).encode(ENCODING)


class Array(TypeBase):
    def __init__(self, elementType):
        self.elementType = TypeBase.getIfBuiltIn(elementType)

    def fromBytes(self, string):
        if string[0] != ord("[") or string[-1] != ord("]"):
            raise ValueError("Not an array: " + string.decode(ENCODING))

        parts = string[1:-1].split(b",")
        return [self.elementType.fromBytes(part) for part in parts]

    def toBytes(self, value):
        return f"[{','.join([self.elementType.toBytes(el) for el in value])}]".encode(ENCODING)
