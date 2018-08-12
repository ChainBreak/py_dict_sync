#!/usr/bin/env python2

import socket
import thread
import threading
import time
import json


class DictSyncServer():
    def __init__(self,host,port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        self.token_dict = {"abc123":{}}

        while True:
            client, addr = sock.accept()
            thread.start_new_thread(self.process_client, (client,))
        sock.close()

    def process_client(self,client):
        #record process start time for detecting time out
        start_time = time.time()
        #create empty message to append to
        msg_str = ""
        #while connected
        while True:
            #read string from client and append to message string
            msg_str += client.recv(1024)
            #look for special character that separates json strings
            i = msg_str.find(chr(255))
            #if the special character is found
            if i > 0:
                #slice out the first json string from the message string
                json_str = msg_str[:i]
                #cut the json string from the front of the message string
                msg_str = msg_str[i+1:]
                #try passing the json string
                try:
                    json_dict = json.loads(json_str)
                    print(json_dict["token"])
                    print(len(json_dict["dict"]))
                except Exception as e:
                    print(e)

            time.sleep(0.01)
            if time.time() - start_time > 1.0:
                break

        client.close()


if __name__ == '__main__':
    DictSyncServer("",12345)
