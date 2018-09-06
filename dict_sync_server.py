#!/usr/bin/env python2

import socket
import thread
import threading
import time
import json

class User():
    def __init__(self):
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

        return "update"

    def state_update(self):
        client_dict = self.recv_dict["dict"]
        server_dict = self.user.dict
        update_dict = self.send_dict["dict"] = {}

        with self.user.lock:
            #TODO: Limit the number of dicts a user can have based on payment package
            #for every dictionary item sent from the client
            for key,(client_trans_count, client_value) in client_dict.items():
                #check if the key already exists
                if key in server_dict:

                    server_trans_count, server_value = server_dict[key]
                    if client_trans_count == -1 or client_trans_count > server_trans_count:
                        new_trans_count = server_trans_count + 1
                        #TODO: record update time to remove old items
                        server_dict[key] = (new_trans_count, client_value)
                        update_dict[key] = (new_trans_count, client_value)

                    elif client_trans_count < server_trans_count:
                        update_dict[key] = (server_trans_count, server_value)
                else:
                    if client_trans_count == -1:
                        #TODO: record update time to remove old items
                        server_dict[key] = (1, client_value)
                        update_dict[key] = (1, client_value)
                    else:
                        server_dict[key] = (client_trans_count, client_value)

        return "send"



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
