from .base_handler import BaseHandler
from .base_types import TypeBase, String

def command(arg):
    def getArgumentTypes(func):
        typedArguments = func.__annotations__

        argumentTypes = []
        for argName in func.__code__.co_varnames[2:]:
            # for every argument of the decorated function the type is obtained (if specified with
            # `argument: type`) or defaulted to `String`. Built-in types are supported.
            argumentType = typedArguments.get(argName, String)
            argumentTypes.append(TypeBase.getIfBuiltIn(argumentType))

        return argumentTypes

    if callable(arg):
        # `@command` used without parameters
        arg.__gpcp_metadata__ = (BaseHandler.FunctionType.command,
                                 arg.__name__, getArgumentTypes(arg))
        return arg

    # `@command` used with name parameter (e.g. @command("start"))
    def wrapper(func):
        func.__gpcp_metadata__ = (BaseHandler.FunctionType.command,
                                  arg, getArgumentTypes(func))
        return func
    return wrapper # the returned function when called adds the metadata to `func` and returns it

def unknownCommand(func):
    func.__gpcp_metadata__ = (BaseHandler.FunctionType.unknown,)
    return func
