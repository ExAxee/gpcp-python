import time
import gpcp
import sys
import random
import threading
import multiprocessing
import logging
logging.basicConfig(filename="./logs.txt", level=logging.DEBUG, force=True)

HOST = "0.0.0.0"
PORT = 9136
CLIENTS = 5

def runServer():
    class ServerHandler(gpcp.BaseHandler):
        @gpcp.command
        def fibonacci(self, i: int) -> int:
            global timesCalled
            timesCalled += 1

            def fib(x):
                if x < 2:
                    return 1
                else:
                    return fib(x-1) + fib(x-2)

            return fib(i)

    global server
    with gpcp.Server(handler=ServerHandler) as server:
        server.startServer(HOST, PORT)

def runClient():
    client = gpcp.Client(HOST, PORT)
    client.loadInterface(client)
    time.sleep(.5) # give the CPU some free time to setup other clients, too
    client.fibonacci(36) # this surely takes enough time (tens of seconds)
    assert False # will never be reached


def test_connection_badly_closed(reraise):
    global timesCalled
    timesCalled = 0

    serverThread = threading.Thread(target=reraise.wrap(runServer), daemon=True)
    serverThread.start()

    time.sleep(0.1) # make sure the server has started

    # use processes instead of threads here, since threads cannot be stopped easily
    clientThreads = [multiprocessing.Process(target=reraise.wrap(runClient), daemon=True) for i in range(CLIENTS)]
    for thread in clientThreads:
        thread.start()

    time.sleep(2) # make sure clients have all connected
    for thread in clientThreads:
        thread.terminate()

    server.stopServer()
    serverThread.join()

    assert timesCalled == CLIENTS
    assert len(threading._active.items()) == 1

if __name__ == "__main__":
    class Reraise:
        def wrap(x):
            return x
    test_connection_badly_closed(Reraise)