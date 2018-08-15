#!/usr/bin/env python2
import json
import threading
import time
import socket

class SyncDict():
    def __init__(self,name,token,server_addr="127.0.0.1",server_port=12345):
        self.name = name
        self.token = token
        self.trans_count = 0
        self.host = server_addr
        self.port = server_port

        self.dict = {}
        self.update_dict = {}
        self.dict_lock = threading.Lock()

        self.sync_thread = threading.Thread(target=self.sync_loop)
        self.sync_thread.daemon = True

    def sync_loop(self):
        self.sock = None
        self.recv_str = ""
        def wait():
            time.sleep(1.0)
            return "connect"

        def connect():
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((self.host,self.port))
            return "send"

        def send():
            with self.dict_lock:
                send_dict = {
                    "name":self.name,
                    "token":self.token,
                    "trans_count":self.trans_count,
                    "dict":self.update_dict
                }

                send_str = json.dumps(send_dict) + chr(255)
                self.sock.sendall(send_str)
                self.update_dict = {}
            return "recv"

        def recv():
            self.recv_str += self.sock.recv(1024)
            
            if len(self.recv_str) > 0:
                if self.recv_str[-1] == chr(255):
                    recv_dict = json.loads(self.recv_str[:-1])
                    self.recv_str = ""

                    with self.dict_lock:
                        for key,value in recv_dict["dict"].items():
                            self.dict[key] = value


                    self.trans_count = recv_dict["trans_count"]
                    # print(self.trans_count)
                    return "close"

            return "recv"

        def close():
            if not self.sock is None:
                self.sock.close()
            self.sock = None
            self.recv_str = ""
            return "wait"

        states = {
            "wait": wait,
            "connect": connect,
            "send": send,
            "recv": recv,
            "close": close
        }


        state = "wait"
        while self.running:
            try:
                # print(state)
                state = states[state]()
            except Exception as e:
                state = "close"
                print("Error: %s" % e)

            #raw_input("press enter")



    def __enter__(self):
        self.running = True
        self.sync_thread.start()
        return self

    def __exit__(self,*args):
        self.running = False
        self.sync_thread.join()

    def __getitem__(self,key):
        with self.dict_lock as dl:
            return self.dict.get(key,None)

    def __setitem__(self,key,value):
        with self.dict_lock as dl:
            self.dict[key] = self.update_dict[key] =  value

    def __delitem__(self,key):
        pass

    def __len__(self):
        return len(self._dict)




if __name__ == "__main__":
    with SyncDict("my_dict","abc123") as d1:
        with SyncDict("my_dict","abc123") as d2:
            d1["a"] = 1
            d1["b"] = 1
            d2["b"] = 1
            d2["a"] = 1

            while True:
                d1["a"] += 1
                d2["b"] += 1

                print("a %i %i" % ( d1["a"], d2["a"]))
                time.sleep(0.5)
                print("b %i %i" % ( d1["b"], d2["b"]))
                time.sleep(0.5)
