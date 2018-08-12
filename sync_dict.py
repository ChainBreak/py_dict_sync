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
        while self.running:
            time.sleep(1.0)

            with self.dict_lock as dl:
                update_dict_copy = self.update_dict
                self.update_dict = {}

            msg_dict = {
                "name":self.name,
                "token":self.token,
                "trans_count":self.trans_count,
                "dict":update_dict_copy
            }

            msg_str = json.dumps(msg_dict) + chr(255) 

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                sock.connect((self.host,self.port))
                sock.sendall(msg_str)
                print(len(msg_str))

            except Exception as e:
                print("ethernet error")
                print(e)
                with self.dict_lock as dl:
                    update_dict_copy.update(self.update_dict)
                    self.update_dict = update_dict_copy
            finally:
                sock.close()

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
    with SyncDict("my_dict","abc123") as d:
        d["zero"] = 0
        d["one"] = 1
        d["two"] = 2
        d["list"] = [1,2,3]
        d["dict"] = {"test":1}

        d["counter"] = 0

        while True:
            for i in range(300):
                d[str(i)] = i
            time.sleep(0.1)
