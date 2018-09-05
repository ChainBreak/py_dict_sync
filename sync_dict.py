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
        self.host = server_addr
        self.port = server_port

        self.dict = {}
        self.dict_lock = threading.Lock()

        self.sync_thread = threading.Thread(target=self.sync_loop)
        self.sync_thread.daemon = True

    def sync_loop(self):
        self.sock = None
        self.recv_str = ""

        def state_wait():
            time.sleep(self.sync_delay)
            return "connect"

        def state_connect():
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.0)
            self.sock.connect((self.host,self.port))
            return "send"

        def state_send():
            with self.dict_lock:

                send_dict = {
                    "token":self.token,
                    "dict": self.dict,
                }

                send_str = json.dumps(send_dict) + chr(255)

                self.sock.sendall(send_str)
                self.update_dict = {}
            return "recv"


        def state_recv():
            self.recv_str += self.sock.recv(1024)

            if len(self.recv_str) > 0:
                if self.recv_str[-1] == chr(255):
                    recv_dict = json.loads(self.recv_str[:-1])
                    self.recv_str = ""

                    with self.dict_lock:
                        for key,(trans_count,value) in recv_dict["dict"].items():
                            self.dict[key] = (trans_count,value)

                    return  "close"

            return "recv"

        def state_close():
            if not self.sock is None:
                self.sock.close()
            self.sock = None
            self.recv_str = ""
            return "wait"

        states = {
            "wait": state_wait,
            "connect": state_connect,
            "send": state_send,
            "recv": state_recv,
            "close": state_close
        }


        state = "wait"
        while self.running:
            try:
                # print(state)
                # time.sleep(0.5)
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
            if key in self.dict:
                _,value = self.dict[key]
                return value
            else:
                self.dict[key] = (0,None)
                return None

    def __setitem__(self,key,value):
        with self.dict_lock:
            self.dict[key] = (-1,value)

    def __delitem__(self,key):
        with self.dict_lock:
            del self.dict[key]

    def __len__(self):
        return len(self._dict)

    def __str__(self):
        with self.dict_lock:
            msg = ""
            for key,(trans_count,value) in self.dict.items():
                msg += "%s, %s, %s\n" % (key,str(trans_count),str(value))
            return msg
