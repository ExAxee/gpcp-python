import time
import threading
import gpcp
import sys

HOST = "0.0.0.0"
PORT = 9134
SLEEP_SECONDS = 8

def runServer():
    class ServerHandler(gpcp.BaseHandler):
        @gpcp.command
        def waitSomeTime(self) -> None:
            time.sleep(SLEEP_SECONDS)

    global server
    with gpcp.Server(handler=ServerHandler) as server:
        server.startServer(HOST, PORT)

def runClient():
    with gpcp.Client(HOST, PORT) as client:
        client.loadInterface(client)
        client.waitSomeTime()


def test_longTimeout(reraise):
    serverThread = threading.Thread(target=reraise.wrap(runServer))
    serverThread.start()

    clientThreads = [threading.Thread(target=reraise.wrap(runClient)) for i in range(5)]
    for thread in clientThreads:
        thread.start()

    startTime = time.time()
    for thread in clientThreads:
        thread.join()
    takenTime = time.time() - startTime
    assert takenTime < 2 * SLEEP_SECONDS

    server.stopServer()
    serverThread.join()