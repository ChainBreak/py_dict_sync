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
    def __init__(self,server,client_sock):


        #record process start time for detecting time out
        start_time = time.time()


        def case_init():

            self.recv_str = ""
            self.recv_dict = {}
            self.send_dict = {}
            self.user = None
            self.named_dict = None
            return "recv"

        def case_recv():
            #read string from client and append to message string
            self.recv_str += client_sock.recv(1024)
            if len(self.recv_str):
                #TODO: reject client if the string gets to large for performance
                if self.recv_str[-1] == chr(255):
                    self.recv_dict = json.loads(self.recv_str[:-1])
                    return "token"
            time.sleep(0.1)
            return "recv"

        def case_token():
            user_token = self.recv_dict["token"]
            with server.users_lock:
                self.user = server.users_dict[user_token]
            return "user"

        def case_user():
            name = self.recv_dict["name"]
            with self.user.lock:
                if not name in self.user.named_dicts:
                    #TODO: Limit the number of dicts a user can have based on payment package
                    self.named_dict = NamedDict()
                    self.user.named_dicts[name] = self.named_dict
                else:
                    self.named_dict = self.user.named_dicts[name]
            return "named_dict"


        def case_named_dict():

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

        def case_send():
            send_str = json.dumps(self.send_dict) + chr(255)
            client_sock.sendall(send_str)

            return "init"

        states = {
        "init": case_init,
        "recv": case_recv,
        "token": case_token,
        "user": case_user,
        "named_dict": case_named_dict,
        "send": case_send
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
