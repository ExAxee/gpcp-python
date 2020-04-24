import enum
from gpcp.utils.base_types import getIfBuiltIn, Bytes

class FunctionType(enum.Enum):
    command = 0
    unknown = 1

def command(arg):
    """
    Marks the decorated function as a command with a string identifier. Also obtains argument types
    and function return value if they are specified with the `def function(argument: type) -> type`
    syntax, defaulting to `Bytes` for non-specified types. Those types are used to automatically
    convert the values passed to the function. Built-in types are supported.

        :param arg: (optinal) the command identifier for the function,
            defaults to the name of the function if not specified
    """

    def getArgumentTypes(func):
        """
        For every argument of the decorated function the type is obtained (if specified
        with `argument: type`) or defaulted to `Bytes`. Built-in types are supported.
        """

        typedArguments = func.__annotations__
        argumentTypes = []

        for argName in func.__code__.co_varnames[2:]:
            argumentType = typedArguments.get(argName, Bytes)
            argumentTypes.append((getIfBuiltIn(argumentType), argName))

        return argumentTypes

    def getReturnType(func):
        """
        Obtains the return type of a function (if specified with `def function() -> type:`)
        defaulting to `Bytes`. Built-in types are supported.
        """

        returnType = func.__annotations__.get("return", Bytes)
        return getIfBuiltIn(returnType)


    if callable(arg):
        # `@command` used without parameters
        arg.__gpcp_metadata__ = (FunctionType.command, arg.__name__,
                                 arg.__doc__, getReturnType(arg), getArgumentTypes(arg))
        return arg

    # `@command` used with name parameter (e.g. @command("start"))
    def wrapper(func):
        func.__gpcp_metadata__ = (FunctionType.command, arg,
                                  func.__doc__, getReturnType(func), getArgumentTypes(func))
        return func
    return wrapper # the returned function when called adds the metadata to `func` and returns it

def unknownCommand(func):
    func.__gpcp_metadata__ = (FunctionType.unknown,)
    return func
