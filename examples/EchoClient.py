from gpcp.client import Client

def my_handler(connection, data):
    """This is the handler who is called when a response from the server is received"""
    print(str(data, "utf-8")) #The response will be returned in bytes so it's up to you to encode these bytes

client = Client(default_handler=my_handler)
#initialize the client and assign the handler

client.connect("localhost", 7530)
#connect to a server

inpt = str(input(">>> "))
client.request(inpt)
#make the request

client.closeConnection()
#disconnect from the server