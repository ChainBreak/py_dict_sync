#!/usr/bin/env python2
import json
import threading
import time
import socket

class SyncDict():
    def __init__(self,name,token, sync_delay = 1.0, server_addr="127.0.0.1",server_port=12344):
        self.name = name
        self.token = token
        self.sync_delay = sync_delay
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

        def case_wait():
            time.sleep(self.sync_delay)
            return "connect"

        def case_connect():
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((self.host,self.port))
            return "send"


        def case_send():
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


        def case_recv():
            self.recv_str += self.sock.recv(1024)

            if len(self.recv_str) > 0:
                if self.recv_str[-1] == chr(255):
                    recv_dict = json.loads(self.recv_str[:-1])
                    self.recv_str = ""

                    with self.dict_lock:
                        for key,value in recv_dict["dict"].items():
                            self.dict[key] = value

                    next_state = "close"
                    if self.trans_count > recv_dict["trans_count"]:
                        self.update_dict.update(self.dict)
                        next_state = "send"

                    self.trans_count = recv_dict["trans_count"]

                    return next_state

            return "recv"

        def case_close():
            if not self.sock is None:
                self.sock.close()
            self.sock = None
            self.recv_str = ""
            return "wait"

        states = {
            "wait": case_wait,
            "connect": case_connect,
            "send": case_send,
            "recv": case_recv,
            "close": case_close
        }


        state = "wait"
        while self.running:
            try:
                # print(state)
                state = states[state]()
            except Exception as e:
                state = "close"
                print("Error: %s" % e)



    def __enter__(self):
        self.running = True
        self.sync_thread.start()
        return self

    def __exit__(self,*args):
        self.running = False
        self.sync_thread.join()

    def __getitem__(self,key):
        with self.dict_lock:
            return self.dict.get(key,None)

    def __setitem__(self,key,value):
        with self.dict_lock:
            self.dict[key] = self.update_dict[key] =  value

    def __delitem__(self,key):
        pass

    def __len__(self):
        return len(self._dict)

    def __str__(self):
        with self.dict_lock:
            return str(self.dict)
