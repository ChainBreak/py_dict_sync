#!/usr/bin/env python2
from sync_dict import SyncDict
import time
if __name__ == "__main__":
    with SyncDict("my_dict","abc123",sync_delay=0.1) as d:
        d["b1"] = 1
        d["b2"] = 0

        d["a1"]
        d["a2"]
        while True:
            d["b1"] += 1
            print(str(d))

            time.sleep(0.5)
