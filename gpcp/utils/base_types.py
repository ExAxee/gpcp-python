class TypeBase:
    @staticmethod
    def serialize(value):
        raise NotImplementedError()

    @staticmethod
    def deserialize(entry):
        raise NotImplementedError()

class NoneType:
    @staticmethod
    def serialize(value):
        return None # will translate to `null` in json

    @staticmethod
    def deserialize(entry):
        return None

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

class String(JsonBuiltinType):
    pass

class Boolean(JsonBuiltinType):
    pass

class Integer(JsonBuiltinType):
    pass

class Float(JsonBuiltinType):
    pass

class JsonObject(JsonBuiltinType):
    pass

class JsonArray(JsonBuiltinType):
    pass


def getIfBuiltIn(argumentType):
    """
    If needed converts built-in types into the corresponding TypeBase
        :param argumentType: a type to convert if it's a built-in one
    """

    if argumentType is None:
        return NoneType
    if argumentType == dict:
        return JsonObject
    if argumentType == list:
        return JsonArray
    if argumentType == str:
        return String
    if argumentType == bool:
        return Boolean
    if argumentType == int:
        return Integer
    if argumentType == float:
        return Float
    if argumentType == bytes:
        return Bytes
    return argumentType

# DO NOT MODIFY THE ORDER OF THIS ARRAY unless you also change the IDs in all other implementations
allTypesArray = [NoneType, JsonObject, JsonArray, String, Boolean, Integer, Float, Bytes]

def getFromId(integerId: int) -> type:
    """
    Returns the BaseType corresponding to id, by looking into the `allTypesArray` array
        :param integerId: an int smaller than the size of the array
    """
    return allTypesArray[integerId]

def toId(baseType: type) -> int:
    """
    Returns the id corresponding to the BaseType, by taking its index in the `allTypesArray` array
        :param baseType: a BaseType existing in the array
        :returns: an integer identifier
    """
    return allTypesArray.index(baseType)
