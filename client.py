import socket

global HEADER
HEADER = 4

class Client:
    
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def startclient(self, port=7530):
        self.socket.connect( (socket.gethostname(), port) )
        print(f"Connected!")
        
        try:
            while 1:
                self.full_msg = ""
                self.new_msg = True
                while 1:
                    self.msg = self.socket.recv(16)
                    if self.new_msg:
                        self.msg_len = int(self.msg[:HEADER])
                        print(f"Message of len {self.msg_len} recived")
                        self.new_msg = False
                              
                    self.full_msg += self.msg.decode("utf-8")
                    
                    if len(self.full_msg) - HEADER == self.msg_len:
                        print(self.full_msg)
                        print("Full message recived")
                        self.new_msg = True
                        self.full_msg = ""
        
        except:
            print("Some error has occurred, closing connections.")
            self.socket.shutdown(socket.SHUT_RDWR)
           self.socket.close()