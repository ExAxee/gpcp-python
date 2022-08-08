import time
import threading
import gpcp
import sys
import random

HOST = "0.0.0.0"
PORT = 9135
SECONDS = 5
CLIENTS = 32

FIBONACCI = [
    1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946,
    17711, 28657, 46368, 75025, 121393, 196418, 317811, 514229, 832040, 1346269, 2178309, 3524578,
    5702887, 9227465, 14930352, 24157817, 39088169, 63245986, 102334155
]

def runServer():
    class ServerHandler(gpcp.BaseHandler):
        @gpcp.command
        def fibonacci(self, i: int) -> int:
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
    with gpcp.Client(HOST, PORT) as client:
        client.loadInterface(client)

        initialTime = time.time()
        while time.time() - initialTime < SECONDS:
            i = random.randint(25, 31)
            assert client.fibonacci(i) == FIBONACCI[i]


def test_stress(reraise):
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
    assert takenTime < 8 * SECONDS

    server.stopServer()
    serverThread.join()
    assert len(threading._active.items()) == 1
