from socket import timeout as socket_timeout
from threading import Event, Thread
import logging
from gpcp.core import packet

logger = logging.getLogger(__name__)

class BufferEvent:
    def __init__(self):
        self.update = Event()
        self.buffer = []

    def waitForUpdate(self, timeout=5):
        if len(self.buffer) != 0:
            return self.buffer.pop(0)

        self.update.wait(timeout)
        if len(self.buffer) != 0:
            return self.buffer.pop(0)

        self.update.clear()
        raise TimeoutError()

class Dispatcher:

    def __init__(self, socket, timeout: float = 0.1):
        #initialize the event triggers
        self.request = BufferEvent()
        self.response = BufferEvent()
        self.socket = socket
        self.socket.settimeout(timeout)
        self._stop = False

        self.thread = Thread(target=self.startReceiver)
        self.thread.setName(f"{self.socket.getsockname()} dispatcher")
        self.thread.start()

    def startReceiver(self):
        while not self._stop:
            self.request.update.clear()
            self.response.update.clear()

            try:
                data, isRequest = packet.receiveAll(self.socket)
            except TimeoutError:
                continue

            if data is None: # connection was closed
                logger.debug(f"received None from {self.socket.getpeername()}, terminating dispatcher")
                self.request.buffer.append(None)
                self.response.buffer.append(None)

                self.request.update.set()
                self.response.update.set()

                self._stop = True

            else:
                if isRequest:
                    logger.debug(f"received request: {data}")
                    self.request.buffer.append(data)
                    self.request.update.set()
                else:
                    logger.debug(f"received response: {data}")
                    self.response.buffer.append(data)
                    self.response.update.set()

    def setStopFlag(self):
        self.request.update.set()
        self.response.update.set()
        self._stop = True
