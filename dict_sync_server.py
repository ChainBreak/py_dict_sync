#!/usr/bin/env python2

# import socket programming library
import socket

# import thread module
import thread
import threading
import time


class DictSyncServer():
    def __init__(self,host,port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        while True:
            client, addr = sock.accept()
            thread.start_new_thread(self.process_client, (client,))
        sock.close()

    def process_client(self,client):
        start_time = time.time()
        msg_str = ""
        while True:
            data = client.recv(1024)
            
            msg_str += data
            # print "data"
            # print(data)
            time.sleep(0.01)
            if time.time() - start_time > 1.0:
                break
            # send back reversed string to client
            #client.send(data)

        print(data)
        # connection closed
        client.close()


if __name__ == '__main__':
    DictSyncServer("",12345)
