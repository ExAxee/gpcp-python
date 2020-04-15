from gpcp.client import Client
from gpcp.utils.base_handler import BaseHandler
from gpcp.utils.filters import command, unknownCommand

#this is the function that will handle our data
def handler(sock, data):
    print(data)

#same as the server-side, you can use with statement to make sure
#to close correctly the client
with Client(default_handler=handler) as client:
    client.connect("localhost", 7530) #connect the client to the server

    while True:
        inpt = input("cmd >>> ") #take in input a command from the user
        #try to write "echo hello world!"
        client.request(inpt) #make the request
