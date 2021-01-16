from gpcp.utils.handlerValidator import validateHandler
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

    def connect(self, host: str, port: int):
        """
        Connect to a server

        :param host: the host server ip or address
        :param port: the port on the host server
        :returns: self, so that this function can be called inside a `with`
        """

        logger.info(f"connect() called with host={host}, port={port}")

        if not isinstance(host, str):
            raise ConfigurationError(f"invalid option '{host}' for host, must be string")
        if not isinstance(port, int):
            raise ConfigurationError(f"invalid option '{port}' for port, must be integer")

        self.socket.connect((host, port))
        self.localAddress = self.socket.getsockname()
        self.remoteAddress = self.socket.getpeername()

        # setting up initial data to send
        config = json.dumps({
            "role":self._gpcpRole
        })

        # initial data transfer
        packet.sendAll(self.socket, config)
        logger.debug(f"remote config sent to {self.remoteAddress}: {config}")
        remoteConfig = json.loads(packet.receiveAll(self.socket)[0])
        logger.debug(f"remote config recieved on {self.localAddress}: {remoteConfig}")

        # checking config validity
        if remoteConfig["role"] not in ["R", "A", "AR", "RA"]:
            logger.error(f"invalid configuration argument '{remoteConfig['role']}' for 'role' in connection {self.remoteAddress}, closing")
            self.socket.close()

        # checking if the endpoints can actually talk to each other
        if remoteConfig["role"] == "R" and self._gpcpRole == "R":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only respond, closing")
            self.socket.close()
        elif remoteConfig["role"] == "A" and self._gpcpRole == "A":
            logger.warning(f"both local {self.localAddress} and remote {self.remoteAddress} endpoints can only request, closing")
            self.socket.close()
        
        # locking the handler if needed
        if self._gpcpRole == "A":
            self.handler._LOCK = True
        else:
            self.handler._LOCK = False

        #setting up the thread
        self._mainLoopThread = Thread(target=self.mainLoop)
        self._mainLoopThread.setName(f"connection ({self.socket.getpeername()[0]}:{self.socket.getpeername()[1]})")
        self._mainLoopThread.start()

        return self

    def __init__(self, role = "A", handler = None):
        logger.debug(f"__init__() called with handler={handler}")

        if role == "R":
            self._gpcpRole = role
        elif role == "A":
            self._gpcpRole = role
        elif role == "AR" or role == "RA":
            self._gpcpRole = role
        else:
            raise ConfigurationError(f"invalid server role for {self.__class__.__name__}: options are ['A', 'R', 'RA' | 'AR']")

        if handler:
            self.handler = validateHandler(handler)()
        else:
            self.handler = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._stop = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.closeConnection()
