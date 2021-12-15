import pprint
from datetime import datetime
import time
import os
import sys
import json
import requests
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
from filelock import FileLock
import cryptocompare
import sqlite3
import configparser

cryptocompare.cryptocompare._set_api_key_parameter("-")

wishlist = []
#node_url = 'http://eeebox:18084/json_rpc'
config = configparser.ConfigParser()
config.read('wishlist.ini')
node_url = "http://localhost:" + config["monero"]["daemon_port"] + "/json_rpc"

json_fname = os.path.join(config["wishlist"]['www_root'],"data","wishlist-data.json")


def getPrice(crypto,offset):
    data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
    #print(f"[{crypto}]:{data[str(crypto)]['USD']}")
    value = float(data[str(crypto)]["USD"])
    #print(f"value = {value}")
    return(float(value) - (float(value) * float(offset)))

def getJson():
    #must get the latest json as it may have been changed
    global json_fname
    with open(json_fname) as json_file:
        data = json.load(json_file)
        return data

def main(tx_id,multi=0):
    #check height
    #print("Get json")
    saved_wishlist = getJson()
    #pprint.pprint(saved_wishlist)
    if multi == 0:
        #print("multi = 0")
        tx_data = checkHeight(tx_id)
    else:
        tx_data = tx_id
    if tx_data:
        #print(f"we got funds : {tx_data['address']}")
        tx_data["amount"] = formatAmount(tx_data["amount"])
        found = 0
        main_fund = saved_wishlist["metadata"]["total"]
        for i in range(len(saved_wishlist["wishlist"])):
            try:
                #print(saved_wishlist[i])
                if saved_wishlist["wishlist"][i]["xmr_address"] == tx_data["address"]:
                    found = 1
                    saved_wishlist["wishlist"][i]["modified_date"] = str(datetime.now())
                    #contributor += 1 
                    saved_wishlist["wishlist"][i]["contributors"] += 1
                    #total += amount
                    saved_wishlist["wishlist"][i]["xmr_total"] += float(tx_data["amount"])
                    history_tx = {
                    "amount":float(tx_data["amount"]),
                    "date_time": str(datetime.now())
                    }
                    saved_wishlist["wishlist"][i]["history"].append(history_tx)
                    #Percent calculated by JS - or some timed script to periodically check         
                    break
            except Exception as e:
                raise e
        if found == 0:
            extra_xmr = tx_data["amount"]
            #donation received on invalid wishlist
            saved_wishlist["metadata"]["total"] += float(extra_xmr)
            saved_wishlist["metadata"]["contributors"] += 1

        saved_wishlist["wishlist"] = sorted(saved_wishlist["wishlist"], key=lambda k: k['percent'],reverse=True)
        modified = str(datetime.now())
        saved_wishlist["metadata"]["modified"] = modified
        dump_json(saved_wishlist)

def dump_json(wishlist):
    global json_fname
    lock = json_fname + ".lock"
    with FileLock(lock):
        #print("Lock acquired.")
        with open(json_fname, 'w+') as f:
            json.dump(wishlist, f, indent=6)  

# should be check - exists in database
def checkHeight(tx_id):
    global node_url
    #loop incase rpc daemon has not started up yet.
    retries = 0
    while True:
        try:
            print("Trying to download from rpc")
            rpc_connection = AuthServiceProxy(service_url=node_url)
            print("after rpc con")
            print(tx_id)
            params = {
                      "account_index":0,
                      "in":True
                     }
            info = rpc_connection.get_transfers(params)
            pprint.pprint(info)
            params = {
                      "account_index":0,
                      "txid":tx_id
                     }
            info = rpc_connection.get_transfer_by_txid(params)
            pprint.pprint(info)
            break
        except (requests.HTTPError,
          requests.ConnectionError,
          JSONRPCException) as e:
            if retries > 10:
                print("error: monero rpc connection failed")
                break
            else:
                print(e)
                #print("Retrying connection in 5 seconds.")
                time.sleep(5)
    if len(info['transfers']) == 1:
        con = sqlite3.connect('xmr_ids.db')
        cur = con.cursor()
        create_tx_ids_table = """ CREATE TABLE IF NOT EXISTS txids (
                                    id text PRIMARY KEY
                                ); """
        cur.execute(create_tx_ids_table)
        con.commit()
        cur.execute('SELECT * FROM txids WHERE id = ?',[tx_id])
        rows = len(cur.fetchall())
        if rows == 0:
            sql = ''' INSERT INTO txids(id)
                      VALUES(?) '''
            cur.execute(sql, (tx_id,))
            con.commit()
            return info["transfer"]
        cur.close()
    else:
        for x in info["transfers"]:
                main(x,1)

def formatAmount(amount):
    """decode cryptonote amount format to user friendly format.
    Based on C++ code:
    https://github.com/monero-project/bitmonero/blob/master/src/cryptonote_core/cryptonote_format_utils.cpp#L751
    """
    CRYPTONOTE_DISPLAY_DECIMAL_POINT = 12
    s = str(amount)
    if len(s) < CRYPTONOTE_DISPLAY_DECIMAL_POINT + 1:
        # add some trailing zeros, if needed, to have constant width
        s = '0' * (CRYPTONOTE_DISPLAY_DECIMAL_POINT + 1 - len(s)) + s
    idx = len(s) - CRYPTONOTE_DISPLAY_DECIMAL_POINT
    s = s[0:idx] + "." + s[idx:]

    #my own hack to remove trailing 0's, and to fix the 1.1e-5 etc
    trailing = 0
    while trailing == 0:
        if s[-1:] == "0":
            s = s[:-1]
        else:
            trailing = 1
    return s

if __name__ == '__main__':
    tx_id = sys.argv[1]
    main(tx_id)
