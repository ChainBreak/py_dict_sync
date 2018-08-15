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

    def process_dict(self,recv_dict):
        send_dict = {}
        if "name" in recv_dict:
            name = recv_dict["name"]

            with self.lock:
                if not name in self.named_dicts:
                    named_dict = NamedDict()
                    self.named_dicts[name] = named_dict
                else:
                    named_dict = self.named_dicts[name]

            send_dict = named_dict.process_dict(recv_dict)
        return send_dict



class NamedDict():
    def __init__(self):
        self.trans_count = 0
        self.dict = {"test":(4,"cheese")}
        self.lock = threading.Lock()

    def process_dict(self,recv_dict):
        send_dict = {}
        try:

                client_dict = recv_dict["dict"]
                client_trans_count = recv_dict["trans_count"]


                with self.lock:

                    if client_trans_count > self.trans_count:
                        self.trans_count = client_trans_count

                    send_dict["dict"] = {}
                    for key, (trans_count,value) in self.dict.items():
                        if trans_count > client_trans_count:
                            send_dict["dict"][key] = value
                            print("returning: %s %s" % (key,value))

                    self.trans_count += 1
                    send_dict["trans_count"] = self.trans_count

                    for key,value in client_dict.items():
                        self.dict[key] = (self.trans_count,value)



        except Exception as e:
            print(e)
        return send_dict



class DictSyncServer():
    def __init__(self,host,port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)
        self.lock = threading.Lock()
        self.user_dict = {"abc123":User()}

        while True:
            client_sock, addr = sock.accept()

            thread.start_new_thread(self.process_client, (client_sock,))
        sock.close()



    def process_client(self,client_sock):
        #record process start time for detecting time out
        start_time = time.time()
        #create empty message to append to
        recv_str = ""
        #while connected
        while True:
            #read string from client and append to message string
            recv_str += client_sock.recv(1024)
            #if the special character is found
            if len(recv_str)>0:
                if recv_str[-1] == chr(255):

                    no_errors = True
                    try:
                        recv_dict = json.loads(recv_str[:-1])
                    except Exception as e:
                        print(e)
                        no_errors = False

                    if no_errors:
                        try:
                            token = recv_dict["token"]
                            with self.lock:
                                    user = self.user_dict[token]
                        except Exception as e:
                            print(e)
                            no_errors = False

                    if no_errors:
                        send_dict = user.process_dict(recv_dict)

                        send_str = json.dumps(send_dict) + chr(255)
                        client_sock.sendall(send_str)
                    recv_str = ""


            time.sleep(0.01)
            if time.time() - start_time > 1.0:
                break

        client_sock.close()


if __name__ == '__main__':
    DictSyncServer("",12345)
