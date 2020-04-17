from gpcp.server import Server
from gpcp.utils.base_handler import BaseHandler
from gpcp.utils.filters import command, unknownCommand

#define the class handler which will handle all requests
#NOTE: you ALWAYS have to return something!!!!
class Handler(BaseHandler): #inherit base properties

    #when there is only command the name of the function
    #will be the same as the funciton call
    @command 
    def echo(self, cmd, *args): #the handler will return always something
        print(*args)
        return str(*args, "utf-8").upper()

    @command("start")
    def my_func(self, cmd, param):
        #if you want that the function requires only one parameter you can
        #define only one argument, but it will throw an error if you give it
        #more than the number defined 

        if param == b"yes":
            return str("yes")
        elif param == b"no":
            return str("no")

    #unknownCommand is called every time a command was not registered on the
    #handler and the server does not know what to do
    @unknownCommand
    def boh(self, cmd, *args):
        print(cmd, *args)
        return "unknown"

#you can use a with statement to make sure that on error the server will close
#correctly
with Server(reuse_addr=True) as server:
    server.setHandlerClass(Handler) #set the handler which the server will use
    server.startServer("localhost", 7530) #then connect the server
