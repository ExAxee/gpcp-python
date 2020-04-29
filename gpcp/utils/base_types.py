from gpcp.utils import packet

class TypeBase:
    @staticmethod
    def serialize(value):
        raise NotImplementedError()

    @staticmethod
    def deserialize(entry):
        raise NotImplementedError()

class JsonBuiltinType(TypeBase):
    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def deserialize(entry):
        return entry

class Bytes(TypeBase):
    @staticmethod
    def serialize(value):
        return value.decode("ascii")

    @staticmethod
    def deserialize(entry):
        return entry.encode("ascii")

class String(JsonBuiltinType): pass
class Integer(JsonBuiltinType): pass
class Float(JsonBuiltinType): pass
class Json(JsonBuiltinType): pass


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

allTypesArray = [Bytes, String, Integer, Float, Json]

def getFromId(integerId: int):
    """
    Returns the BaseType corresponding to id, by looking into the `allTypesArray` array
        :param integerId: an int smaller than the size of the array
    """
    return allTypesArray[integerId]

def toId(baseType: type):
    """
    Returns the id corresponding to the BaseType, by taking its index in the `allTypesArray` array
        :param baseType: a BaseType existing in the array
    """
    return allTypesArray.index(baseType)
