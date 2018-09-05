#!/usr/bin/env python2
from sync_dict import SyncDict
import time
if __name__ == "__main__":
    with SyncDict("my_dict","abc123",sync_delay=0.1) as d:
        d["a1"] = 1
        d["a2"] = 0
        d["b1"]
        d["b2"]
        while True:

            print(str(d))
            d["a1"] += 1
            time.sleep(1)
