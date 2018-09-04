#!/usr/bin/env python2

import socket
import thread
import threading
import time
import json

class User():
    def __init__(self):
        self.named_dicts = {}
        self.lock = threading.Lock()



class NamedDict():
    def __init__(self):
        self.trans_count = 0
        self.dict = {}
        self.lock = threading.Lock()



class ClientHandler():
    """This class is instaciated for every client that connects to the server.
    Its job is handle the data sent from the client and to send resonses"""

    def __init__(self,server,client_sock):
        """The client is handled within the init method
        """
        self.server = server
        self.client_sock = client_sock

        #record start time for detecting time out
        start_time = time.time()

        states = {
        "init": self.state_init,
        "recv": self.state_recv,
        "lookup_user": self.state_lookup_user,
        "get_dict": self.state_get_dict,
        "update": self.state_update,
        "send": self.state_send
        }

        state = "init"

        #while connected
        while time.time() - start_time < 2.0:
            try:
                state = states[state]()
            except Exception as e:
                print e
                #TODO: Return errors to the client

                state = "init"
        client_sock.close()


    # The client is handled with a state machine. States are the following methods

    def state_init(self):
        """Initialise State - just clear the variables"""

        self.recv_str = "" #accumulates the strings received from the client
        self.recv_dict = {} #holds the dict parsed from the client
        self.send_dict = {} #holds the dict to send back to the client
        self.user = None #holds the user object for the token given
        self.named_dict = None #holds the named dict for the dict name given
        return "recv" #goto the recv state

    def state_recv(self):
        """Receive State - accumlates strings recived from the client until the special character
        is recived, then it parses the accumlated string as json"""

        #read string from client and append to message string
        self.recv_str += self.client_sock.recv(1024)

        #if characters have been recieved
        if len(self.recv_str):
            #TODO: reject client if the string gets to large for performance

            #check if the last character is the special character
            if self.recv_str[-1] == chr(255):
                #parse the string (excluding special character)
                self.recv_dict = json.loads(self.recv_str[:-1])

                #goto the token lookup state
                return "lookup_user"

        #if special character wasn't received then loop back to this state
        time.sleep(0.1)
        return "recv"

    def state_lookup_user(self):
        """Lookup User State - Get the user token from the recv_dect then use it
        to lookup the user"""

        #Get token
        user_token = self.recv_dict["token"]

        #lock the users_dict then get the user for this token
        with self.server.users_lock:
            self.user = self.server.users_dict[user_token]

        return "get_dict"

    def state_get_dict(self):
        name = self.recv_dict["name"]
        with self.user.lock:
            if not name in self.user.named_dicts:
                #TODO: Limit the number of dicts a user can have based on payment package
                self.named_dict = NamedDict()
                self.user.named_dicts[name] = self.named_dict
            else:
                self.named_dict = self.user.named_dicts[name]
        return "update"


    def state_update(self):

        client_update_dict = self.recv_dict["dict"]
        client_trans_count = self.recv_dict["trans_count"]

        with self.named_dict.lock:
            self.send_dict["dict"] = {}
            #iterate through the servers named dict and collect everything that is ahead of the client
            for key, (trans_count,value) in self.named_dict.dict.items():
                if trans_count > client_trans_count:
                    self.send_dict["dict"][key] = value

            #increment the servers transaction counter for this named dict
            self.named_dict.trans_count += 1
            self.send_dict["trans_count"] = self.named_dict.trans_count

            for key,value in client_update_dict.items():
                self.named_dict.dict[key] = (self.named_dict.trans_count,value)

        return "send"

    def state_send(self):
        send_str = json.dumps(self.send_dict) + chr(255)
        self.client_sock.sendall(send_str)

        return "init"





class DictSyncServer():
    def __init__(self,host,port):
        #create a new socket and bind it
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        #this lock is used to make sure that only one thread edits the users_dict at one time
        self.users_lock = threading.Lock()

        #initialise the dictionary of users_dict
        #TODO: will need to load user tokens for a database or something
        self.users_dict = {"abc123":User()}

        try:
            print "Dict sync Server Starting"
            #forever
            while True:
                #Accept clients and start client hander objects in their own threads
                client_sock, addr = sock.accept()
                thread.start_new_thread(ClientHandler, (self,client_sock))
        except KeyboardInterrupt:
            pass
        finally:
            #close the socekt
            sock.close()
            print("socket closed")



if __name__ == '__main__':
    DictSyncServer("",12344)
