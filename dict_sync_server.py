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

    def __getitem__(self,key):
        with self.lock as l:
            if not key in self.dict:
                self.dict[key] = NamedDict()
            return self.dict[key]

    def __delitem__(self,key):
        pass

    def __len__(self):
        with self.lock as l:
            return = len(self._dict)

class NamedDict():
    def __init__(self):
        self.trans_count = 0
        self.dict = {}
        self.dict_trans_count = {}
        self.dict_lock = threading.Lock()

    def __getitem__(self,key):
        with self.dict_lock as dl:
            return self.dict.get(key,None)

    def __setitem__(self,key,value):
        with self.dict_lock as dl:
            self.trans_count += 1
            self.dict[key] = value
            self.dict_trans_count = self.trans_count

    def __delitem__(self,key):
        pass

    def __len__(self):
        with self.dict_lock as dl:
            return = len(self._dict)



class DictSyncServer():
    def __init__(self,host,port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        self.user_dict = {"abc123":User()}

        while True:
            client, addr = sock.accept()
            thread.start_new_thread(self.process_client, (client,))
        sock.close()

    def process_dict(self,recv_dict):
        print(recv_dict["token"])
        token = recv_dict["token"]
        name = recv_dict["name"]
        if token in self.user_dict:
            user = self.user_dict[token]
            named_dict = user[name]

        print(recv_dict["dict"])
        send_dict = {}
        return send_dict

    def process_client(self,client):
        #record process start time for detecting time out
        start_time = time.time()
        #create empty message to append to
        recv_str = ""
        #while connected
        while True:
            #read string from client and append to message string
            recv_str += client.recv(1024)
            #if the special character is found
            if len(recv_str)>0:
                if recv_str[-1] == chr(255):

                    try:
                        recv_dict = json.loads(recv_str[:-1])
                        send_dict = self.process_dict(recv_dict)
                        send_str = json.dumps(send_dict)
                        client.sendall(send_str)
                    except Exception as e:
                        print(e)
                    recv_str = ""


            time.sleep(0.01)
            if time.time() - start_time > 1.0:
                break

        client.close()


if __name__ == '__main__':
    DictSyncServer("",12345)
