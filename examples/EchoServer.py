from gpcp.server import Server
import string

def my_request_handler(data, connection):
    print(str(data, "utf-8"))
    return str(data, "utf-8").upper()
    #return the response.
    #NOTE: the handler MUST ALWAYS return something

server = Server(reuse_addr=True)
#Initialize the server, set reuse_addr = True to reuse the address if it's already occupied

server.startServer("localhost", 7530, my_request_handler)
#start the server listening and assign my_request_handler as request handler 