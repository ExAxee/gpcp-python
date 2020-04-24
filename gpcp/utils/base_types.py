import json
from gpcp.utils import packet


class TypeBase:
    # method to override
    @staticmethod
    def fromBytes(string):
        raise NotImplementedError()

    # method to override
    @staticmethod
    def toBytes(value):
        return NotImplementedError()


class Bytes(TypeBase):
    @staticmethod
    def fromBytes(string):
        return string

    @staticmethod
    def toBytes(value):
        return str(value).encode(packet.ENCODING)


class String(TypeBase):
    @staticmethod
    def fromBytes(string):
        return string.decode(packet.ENCODING)

    @staticmethod
    def toBytes(value):
        return value.encode(packet.ENCODING)


class Integer(TypeBase):
    @staticmethod
    def fromBytes(string):
        return int(string.decode(packet.ENCODING), base=10)

    @staticmethod
    def toBytes(value):
        return str(value).encode(packet.ENCODING)


class HexInteger(TypeBase):
    @staticmethod
    def fromBytes(string):
        return int(string.decode(packet.ENCODING), base=16)

    @staticmethod
    def toBytes(value):
        return hex(value).encode(packet.ENCODING)


class Float(TypeBase):
    @staticmethod
    def fromBytes(string):
        return float(string.decode(packet.ENCODING))

    @staticmethod
    def toBytes(value):
        return str(value).encode(packet.ENCODING)


class Json(TypeBase):
    @staticmethod
    def fromBytes(string):
        return json.loads(string.decode(packet.ENCODING))

    @staticmethod
    def toBytes(value):
        return json.dumps(value).encode(packet.ENCODING)


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

allTypesArray = [Bytes, String, Integer, HexInteger, Float, Json]

def getFromId(id: int):
    """
    Returns the BaseType corresponding to id, by looking into the `allTypesArray` array
        :param id: an int smaller than the size of the array
    """
    return allTypesArray[id]

def toId(baseType: type):
    """
    Returns the id corresponding to the BaseType, by taking its index in the `allTypesArray` array
        :param baseType: a BaseType existing in the array
    """
    return allTypesArray.index(baseType)