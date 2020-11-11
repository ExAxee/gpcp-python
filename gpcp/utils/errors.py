class HandlerLoadingError(Exception):
    """
    Raised when something is wrong while loading commands
    as functions in `gpcp.core.base_handler.BaseHandler`.
    If needed it should also be used in custom handlers.
    """

class AnnotationError(Exception):
    """
    Raised when something is wrong while processing
    `@gpcp.utils.annotations.command` or
    `@gpcp.utils.annotations.unknownCommand` annotations
    """

class ConfigurationError(Exception):
    """
    Raised when mistyped or invalid arguments are passed to functions
    """

class UnmetPreconditionError(Exception):
    """
    Raised when some constraint is not followed and an unexpected
    situation happened due to that. Raised, for example, when the
    function annotated as `@gpcp.utils.annotations.unknownCommand`
    does not return bytes.
    """
