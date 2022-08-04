from socket import timeout as socket_timeout
from threading import Thread
from queue import Queue
import logging
from gpcp.core import packet

logger = logging.getLogger(__name__)

class Dispatcher:

    def __init__(self, socket, timeout: float = 0.1):
        #initialize the event triggers
        self.request = Queue()
        self.response = Queue()
        self.socket = socket
        self.socket.settimeout(timeout)
        self._stop = False

        self.thread = Thread(target=self.startReceiver)
        self.thread.name = f"{self.socket.getsockname()} dispatcher"
        self.thread.start()

    def startReceiver(self):
        while not self._stop:
            try:
                data, isRequest = packet.receiveAll(self.socket)
            except TimeoutError:
                continue

            if data is None: # connection was closed
                logger.debug(f"received None from {self.socket.getpeername()}, terminating dispatcher")
                self.stopReceiver()

            else:
                if isRequest:
                    logger.debug(f"received request: {data}")
                    self.request.put(data)
                else:
                    logger.debug(f"received response: {data}")
                    self.response.put(data)

    def stopReceiver(self):
        # sending None to request and response makes sure the endpoint closes, too
        self.request.put(None)
        self.response.put(None)
        self._stop = True
