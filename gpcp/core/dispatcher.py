from socket import timeout as socket_timeout
from threading import Event, Thread
import logging
from gpcp.core import packet

logger = logging.getLogger(__name__)

class Dispatcher:

    def __init__(self, socket, buffer, timeout: float = 0.5):
        #initialize the event triggers
        self.dataBuffer = buffer

        self.socket = socket
        self.socket.settimeout(timeout)
        self._stop = False

        self.thread = Thread(target=self.startReceiver)
        self.thread.setName(f"{self.socket.getsockname()} dispatcher")
        self.thread.start()

    # define functions to be overwritten when needed
    def onKeepAlive(self):
        logger.warning(f"recieved unhandled control packet: {packet.KEEP_ALIVE}")
    
    def onConnectionShutdown(self):
        logger.warning(f"recieved unhandled control packet: {packet.CONN_SHUTDOWN}")
    
    def onRequest(self, data):
        logger.warning(f"recieved unhandled data packet: {packet.STD_REQUEST} with data: {data}")

    def onResponse(self, data):
        logger.warning(f"recieved unhandled data packet: {packet.STD_RESPONSE} with data: {data}")
    # end overwrittable functions

    def startReceiver(self, data):
        while not self._stop:

            try:
                data, pkgType = packet.receiveAll(self.socket) 
            except TimeoutError:
                # keep looping to check self._stop to block the dispatcher
                continue

            # packet.recieve all returns (None, None) if connection is closed
            if data is None and pkgType is None:
                logger.debug(f"received None from {self.socket.getpeername()}, terminating dispatcher")
                self.dataBuffer.buffer.put(None)
                self._stop = True

            # packet.recieve all returns (json, int) if packet is a data packet
            elif data is not None and pkgType is not None:
                if pkgType == packet.STD_REQUEST:
                    logger.debug(f"received request: {data}")
                    self.onRequest(data)
                elif pkgType == packet.STD_RESPONSE:
                    logger.debug(f"received response: {data}")
                    self.onResponse(data)
            
            # packet.recieve all returns (None, int) if packet is control packet
            elif data is None and pkgType is not None:
                if pkgType == packet.KEEP_ALIVE:
                    self.onKeepAlive()
                elif pkgType == packet.CONN_SHUTDOWN:
                    self.onConnectionShutdown()

    def setStopFlag(self):
        self._stop = True
