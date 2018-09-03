#!/usr/bin/env python2
from sync_dict import SyncDict
import time
if __name__ == "__main__":
    with SyncDict("my_dict","abc123") as d:
        d["b"] = 1
        d["b_"] = "b"
        while True:
            d["b"] += 1
            print(str(d.trans_count) + " " +str(d))

            time.sleep(0.5)
