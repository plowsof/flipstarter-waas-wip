import configparser
from filelock import FileLock
from datetime import datetime
import os
import json
config = configparser.ConfigParser()
config.read('./db/wishlist.ini')

def wishlist_usd_notify(db_usd,db_ref_id,db_email,db_fname,db_lname,db_zip,db_street,db_cc,db_order_id,db_date_time):
    global wish_config
    www_root = wish_config["wishlist"]["www_root"]
    wish_id = db_ref_id.split("@")[1]
    data_fname = os.path.join(www_root,"data","wishlist-data.json")

    with open(data_fname, "r") as f:
        data_wishlist = json.load(f)
    found = 0
    found_index = -1
    for i in range(len(data_wishlist["wishlist"])):
        if data_wishlist["wishlist"][i]["id"] == wish_id:
            found = 1
            data_wishlist["wishlist"][i]["usd_total"] += int(db_usd) #in cents i think
            history_tx = {
                "amount":int(db_usd),
                "date_time": str(datetime.now())
            }
            data_wishlist["wishlist"][i]["usd_history"].append(history_tx)
            data_wishlist["wishlist"][i]["contributors"] += 1
            data_wishlist["wishlist"][i]["modified_date"] = str(datetime.now())
            found_index = i
            break
    if found == 1: 
        #save new wishlist with file lock
        lock = data_fname + ".lock"
        with FileLock(lock):
            #print("Lock acquired.")
            with open(data_fname, 'w+') as f:
                json.dump(data_wishlist, f, indent=6)  
    else:
        print("donated to a none existing or archived wish")

    #email alert
    db_wish_id = data_wishlist["wishlist"][found_index]["title"]
    send_email(db_email,db_usd,db_fname,db_crypto_addr,db_zip,db_address,db_date_time,db_refund_addr,db_ticker,db_wish_id)

#def send_email(db_email,db_amount,db_fname,db_crypto_addr,db_zip,db_address,db_date_time,db_refund_addr,db_ticker,db_wish_id):