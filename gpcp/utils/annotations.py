import enum
import re
import keyword
from typing import Callable
from gpcp.utils.base_types import getIfBuiltIn, Bytes
from gpcp.utils.errors import AnnotationError, ConfigurationError

import logging
logger = logging.getLogger(__name__)

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

    def assertIdentifierValid(identifier: str):
        """
        checks if <identifier> is a valid python identifier
        """

        if re.match("^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
            if keyword.iskeyword(identifier):
                raise AnnotationError(f"Invalid command filter '{arg}': it is a python keyword")
        else:
            raise AnnotationError(
                f"Invalid command filter '{arg}': contains special characters or starts with a number"
            )

    def getArgumentTypes(func: Callable):
        """
        For every argument of the decorated function the type is obtained (if specified
        with `argument: type`) or defaulted to `Bytes`. Built-in types are supported.
        """

        typedArguments = func.__annotations__
        argumentTypes = []

        for argName in func.__code__.co_varnames[1:func.__code__.co_argcount]:
            argumentType = typedArguments.get(argName, None)

            if argumentType is None:
                raise ConfigurationError(f"missing argument type for '{argName}' in handler function '{func.__name__}'")

            argumentTypes.append((getIfBuiltIn(argumentType), argName))

        return argumentTypes

    def getReturnType(func: Callable):
        """
        Obtains the return type of a function (if specified with `def function() -> type:`)
        defaulting to `Bytes`. Built-in types are supported.
        """

        returnType = func.__annotations__.get("return", None)

        if returnType is None:
            raise ConfigurationError(f"missing return type for handler function '{func.__name__}'")

        return getIfBuiltIn(returnType)

    def getDescription(func: Callable):
        if func.__doc__ is None:
            return None

        doc = func.__doc__.strip()
        if doc == "":
            return None
        return doc

    # `@command` used without parameters
    if callable(arg):
        assertIdentifierValid(arg.__name__)
        arg.__gpcp_metadata__ = (FunctionType.command, arg.__name__, getDescription(arg),
                                 getReturnType(arg), getArgumentTypes(arg))
        logger.debug(f"@command(): assigned metadata to {arg.__name__}: {arg.__gpcp_metadata__}")
        return arg

    # `@command` used with name parameter (e.g. @command("start"))
    assertIdentifierValid(arg)
    def wrapper(func: Callable):
        func.__gpcp_metadata__ = (FunctionType.command, arg, getDescription(func),
                                  getReturnType(func), getArgumentTypes(func))
        logger.debug(f"@command(\"{arg}\"): assigned metadata to {func.__name__}: {func.__gpcp_metadata__}")
        return func
    return wrapper # the returned function when called adds the metadata to `func` and returns it

def unknownCommand(func: Callable):
    """
    Marks the decorated function as the command to be called when
    the command identifier does not match any other loaded commands.
    Note that the return type should always be `bytes`, otherwise a
    `gpcp.utils.errors.UnmetPreconditionError` will be raised.
    """

    func.__gpcp_metadata__ = (FunctionType.unknown,)
    logger.debug(f"@unknownCommand(): assigned metadata to {func.__name__}: {func.__gpcp_metadata__}")
    return func
