from threading import Event, Thread
from gpcp.core import packet
import logging
import socket

logger = logging.getLogger(__name__)

class Request:
    def __init__(self, event):
        self.update = event
        self.buffer = []
    
    def waitForUpdate(self, timeout=None):
        self.update.wait(timeout)
        return self.buffer.pop(0)

class Response:
    def __init__(self, event):
        self.update = event
        self.buffer = []

    def waitForUpdate(self, timeout=None):
        self.update.wait(timeout)
        return self.buffer.pop(0)

class Dispatcher:

    def __init__(self, socket, request_buffer_update: Event, response_buffer_update: Event, timeout:float = 5):
        #initialize the event triggers
        self.request = Request(request_buffer_update)
        self.response = Response(response_buffer_update)
        self.socket = socket
        self.socket.settimeout(timeout)
        self._stop = False

    def startReceiver(self):
        while not self._stop:
            self.request.update.clear()
            self.response.update.clear()

            data = 0 #initialize data
            try:
                data, isRequest = packet.receiveAll(self.socket)
            except socket.timeout:
                continue

            if data: #trigger only if data has a value different from 0, empty string or None
                if isRequest:
                    logger.debug(f"received request: {data}")
                    self.request.buffer.append(data)
                    self.request.update.set()
                else:
                    logger.debug(f"received response: {data}")
                    self.response.buffer.append(data)
                    self.response.update.set()

            else: #this is None data, meaning connection is closed
                if data == 0: #triggers if data is not updated
                    pass
                if data is None:
                    logger.debug(f"received None from {self.socket.getpeername()}, terminating dispatcher")
                    self.request.buffer.append(None)
                    self.response.buffer.append(None)

                    self.request.update.set()
                    self.response.update.set()

                    self._stop = True

    def stopReceiver(self):
        self._stop = True
