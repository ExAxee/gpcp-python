from gpcp.utils.errors import ConfigurationError
from gpcp.utils.base_types import getFromId
from gpcp.core.dispatcher import Dispatcher
from gpcp.core.endpoint import EndPoint
from threading import Event, Thread
from gpcp.core import packet
from typing import Union
import socket
import json

import logging
logger = logging.getLogger(__name__)

class Client(EndPoint):
    """
    gpcp client main class, used for creating and using a client
    """

    def __init__(self, host: str, port: int, role = "A", handler = None):
        """
        Connect to a server

        :param host: the host server ip or address
        :param port: the port on the host server
        :returns: self, so that this function can be called inside a `with`
        """

        logger.info(f"__init__() called with host={host}, port={port}, role={role}, handler={handler}")

        if not isinstance(host, str):
            raise ConfigurationError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ConfigurationError(f"invalid option '{port}' for port, must be integer")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        super().__init__(sock, role, handler)

        #setting up the thread
        self._mainLoopThread = Thread(target=self.mainLoop)
        self._mainLoopThread.setName(f"connection ({self.socket.getpeername()[0]}:{self.socket.getpeername()[1]})")
        self._mainLoopThread.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.closeConnection()
