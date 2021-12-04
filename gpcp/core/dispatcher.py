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

    def __init__(self, socket, timeout: float = 0.5):
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
                data, pkgType = packet.receiveAll(self.socket) 
            except TimeoutError:
                # keep looping to check self._stop to block the dispatcher
                continue

            # packet.recieve all returns (None, None) if connection is closed
            if data is None and pkgType is None:
                logger.debug(f"received None from {self.socket.getpeername()}, terminating dispatcher")
                self.request.buffer.append(None)
                self.response.buffer.append(None)

                self.request.update.set()
                self.response.update.set()

                self._stop = True

            # packet.recieve all returns (json, int) if packet is a data packet
            elif data is not None and pkgType is not None:
                if pkgType == packet.STD_REQUEST:
                    logger.debug(f"received request: {data}")
                    self.request.buffer.append(data)
                    self.request.update.set()
                elif pkgType == packet.STD_RESPONSE:
                    logger.debug(f"received response: {data}")
                    self.response.buffer.append(data)
                    self.response.update.set()
            
            # packet.recieve all returns (None, int) if packet is control packet
            elif data is None and pkgType is not None:
                if pkgType == packet.KEEP_ALIVE:
                    pass
                elif pkgType == packet.CONN_SHUTDOWN:
                    pass # TODO handle shutdown

    def setStopFlag(self):
        self.request.update.set()
        self.response.update.set()
        self._stop = True
