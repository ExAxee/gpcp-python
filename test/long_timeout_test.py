import time
import threading
import gpcp
import sys

HOST = "0.0.0.0"
PORT = 9134
SECONDS = 8
CLIENTS = 5

def runServer():
    class ServerHandler(gpcp.BaseHandler):
        @gpcp.command
        def waitSomeTime(self) -> None:
            time.sleep(SECONDS)

        @gpcp.command
        def anotherCommand(self, a: str) -> str:
            return a + a

    global server
    with gpcp.Server(handler=ServerHandler) as server:
        server.startServer(HOST, PORT)

def runClient():
    with gpcp.Client(HOST, PORT) as client:
        client.loadInterface(client)
        assert client.anotherCommand("abc") == "abcabc"
        client.waitSomeTime()
        assert client.anotherCommand("abcd") == "abcdabcd"


def test_longTimeout(reraise):
    serverThread = threading.Thread(target=reraise.wrap(runServer), daemon=True)
    serverThread.start()

    time.sleep(0.1) # make sure the server has started

    clientThreads = [threading.Thread(target=reraise.wrap(runClient), daemon=True) for i in range(CLIENTS)]
    for thread in clientThreads:
        thread.start()

    startTime = time.time()
    for thread in clientThreads:
        thread.join()
    takenTime = time.time() - startTime
    assert takenTime < 2 * SECONDS

    server.stopServer()
    serverThread.join()
    assert len(threading._active.items()) == 1
