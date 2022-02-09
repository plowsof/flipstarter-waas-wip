
import json
from filelock import FileLock
import os
import sqlite3
from notify_xmr_vps_pi import db_set_time_wish
import time

wishlist_file = "static/data/wishlist-data.json"
timestamps_db = "timestamps.db"

def main(wish_id):
    global wishlist_file
    if not os.path.isfile(wishlist_file):
        return
    lock = "static/data/wishlist-data.json.lock"
    with FileLock(lock):
        #print("Lock acquired.")
        with open(wishlist_file, 'r') as f:
            wishlist = json.load(f)

        for i in range(len(wishlist["wishlist"])):
            if wishlist["wishlist"][i]["id"] == wish_id:
                if "recurring" in wishlist["wishlist"][i]["type"]:
                    fee = wishlist["wishlist"][i]["type"].split(":")[1]
                    wishlist["wishlist"][i]["usd_total"] -= int(fee)
                    #edit the modified list?
        with open(wishlist_file, 'w') as f:
            json.dump(wishlist, f, indent=6)  
        db_set_time_wish(int(time.time()))

if __name__ == '__main__':
    wish_id = sys.argv[1]
    #wish_id = "73m8nvnhoSME"
    main(wish_id)
