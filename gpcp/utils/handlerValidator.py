from gpcp.core.base_handler import buildHandlerFromFunction
from gpcp.utils.errors import ConfigurationError
from gpcp.core.base_handler import BaseHandler
from typing import Union, Callable
import logging

logger = logging.getLogger(__name__)

def validateHandler(handler: Union[type, Callable]):
        """
        checks for the handler object or function validity

        :param handler: the handler class, usually extending utils.base_handler.BaseHandler
        """

        logger.debug(f"validateHandler() called with handler={handler}")

        #check for handleData core function
        if hasattr(handler, "handleData") and hasattr(handler, "loadHandlers"):
            # this has to be a handler class
            if callable(handler.handleData) and callable(handler.loadHandlers):
                # start the handler loading
                validatedHandler = handler
                validatedHandler.loadHandlers()
                return validatedHandler
            else:
                raise ConfigurationError(
                    f"invalid core method in '{handler.__name__}' for handler class: {'handleData' if not callable(handler.handleData) else 'loadHandlers'} is not callable"
                )
        else:
            # suppose this is a function
            if callable(handler):
                validatedHandler = buildHandlerFromFunction(handler)
                return validatedHandler
            else:
                if isinstance(handler, BaseHandler):
                    raise ConfigurationError(
                        f"missing core method in '{handler.__name__}' for handler class, missing function: \'{'handleData' if not hasattr(handler, 'handleData') else ''}\' \'{'loadHandlers' if not hasattr(handler, 'loadHandlers') else ''}\'"
                    )
                else:
                    raise ConfigurationError(
                        f"{handler.__name__} is neither a handler class nor a function"
                    )
