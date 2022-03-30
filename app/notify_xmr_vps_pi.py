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
sys.path.insert(1, './static')
from static_html_loop import main as static_main
import main as web_main
import asyncio
import uuid
import helper_create
#os.chdir(os.path.dirname(sys.argv[0]))

cryptocompare.cryptocompare._set_api_key_parameter("-")

wishlist = []
#node_url = 'http://eeebox:18084/json_rpc'

local_ip = "localhost"
config = configparser.ConfigParser()
config.read('./db/wishlist.ini')
json_fname = os.path.join(config["wishlist"]['www_root'],"data","wishlist-data.json")

def getJson():
    #must get the latest json as it may have been changed
    global json_fname
    with open(json_fname) as json_file:
        data = json.load(json_file)
        return data

def main(tx_id,multi=0,wow=0):
    #the rpc url should be passed using tx-notify instead, simpler.. todo
    global json_fname
    node_url = "http://" + str(local_ip) + ":" + config["monero"]["daemon_port"] + "/json_rpc"
    wow_node_url = "http://" + str(local_ip) + ":" + config["wow"]["daemon_port"] + "/json_rpc"
    logit(f"node_url = {node_url}")
    logit(f"json fname = {json_fname}")
    if wow == 0:
        atomic_units = 12
        ticker = "xmr"
    else:
        ticker = "wow"
        atomic_units = 11
        node_url = wow_node_url
    saved_wishlist = getJson()
    #pprint.pprint(saved_wishlist)
    if multi == 0:
        #logit("multi = 0")
        tx_data = checkHeight(tx_id,node_url)
    else:
        tx_data = tx_id
    if not tx_data:
        return

    in_amount = formatAmount(tx_data["amount"],atomic_units)
    find_address = tx_data["address"]
    updateDatabaseJson(find_address,in_amount,ticker,saved_wishlist)

def insert_new(address,balance,ticker):
    data = {
    "email": "",
    "amount": float(balance),
    "fname": "",
    "donation_address": address,
    "zipcode": "",
    "address": "",
    "date_time":str(time.time()),
    "refund_address":"",
    "crypto_ticker": ticker, 
    "wish_id": "Unknown",
    "comment": "",
    "comment_name": "",
    "amount_expected":0,
    "consent":"",
    "quantity": "",
    "type":""
    }
    helper_create.db_receipts_add(data)

def updateDatabaseJson(find_address,in_amount,ticker,saved_wishlist,bit_balance=0):
    now = int(time.time())
    db_wish_id = ""
    found = 0
    #bit_balance = balance now for this address
    #old balance = amount in database for this address
    rows = query_address(find_address)
    if len(rows) == 0:
        old_balance = 0
        if ticker == "bch" or ticker == "btc":
            in_amount = float(bit_balance)
        saved_wishlist["metadata"][f"{ticker}_total"] += float(in_amount)
        saved_wishlist["metadata"]["contributors"] += 1
        insert_new(find_address,in_amount,ticker)
        dump_json(saved_wishlist)
        return

    old_balance = rows[0][1]
    if ticker == "bch" or ticker == "btc":
        if old_balance >= bit_balance:
             return
        in_amount = float(bit_balance) - float(old_balance)
    new_balance = float(old_balance) + float(in_amount)
    db_comment_bc = rows[0][16]
    db_comment = rows[0][10]
    db_comment_name = rows[0][11]

    if db_comment_bc == 0 and db_comment != "":
        db_comment_bc = 1
    else:
        db_comment = ""
    set_new_balance(new_balance,db_comment_bc,find_address)

    db_wish_id = rows[0][9]
    if db_wish_id == "Unknown":
        return
    data = add_amount_to_wish(saved_wishlist,db_wish_id,in_amount,ticker)
    saved_wishlist = data["wishlist"]
    saved_wishlist["metadata"]["modified"] = now
    #this is just a global history
    print(f"the comment = {db_comment}")
    comment = {
    "comment": db_comment,
    "comment_name": db_comment_name,
    "date_time": now,
    "usd_value": "",
    "ticker": ticker,
    "amount": in_amount,
    "id": data["title"]
    }
    saved_wishlist["comments"]["comments"].append(comment)
    saved_wishlist["comments"]["modified"] = int(time.time())
    #db_set_time_comment(int(time.time()))
        
    dump_json(saved_wishlist)
    static_main(config)
    uid = uuid.uuid4().hex
    asyncio.run(ws_work_around(uid))

def add_amount_to_wish(saved_wishlist,db_wish_id,in_amount,ticker):
    now = int(time.time())
    for i in range(len(saved_wishlist["wishlist"])):
        general_id = saved_wishlist["wishlist"][i]["id"]
        if saved_wishlist["wishlist"][i]["id"] == db_wish_id:
            found = 1
            saved_wishlist["wishlist"][i]["modified_date"] = now
            saved_wishlist["metadata"]["modified"] = now
            saved_wishlist["wishlist"][i]["contributors"] += 1
            #total += amount
            saved_wishlist["wishlist"][i][f"{ticker}_total"] += float(in_amount)
            history_tx = {
            "amount":float(in_amount),
            "date_time": now
            }
            saved_wishlist["wishlist"][i][f"{ticker}_history"].append(history_tx)
            db_wish_id = saved_wishlist["wishlist"][i]["title"]
            #Percent calculated by JS - or some timed script to periodically check         
            break
    data = {}
    data["wishlist"] = saved_wishlist
    data["found"] = found
    data["realid"] = general_id
    data["title"] = db_wish_id
    return data

async def ws_work_around(uid):
    #set / export environ variable
    con = sqlite3.connect('./db/ws_update.db')
    cur = con.cursor()
    create_modified_table = """ CREATE TABLE IF NOT EXISTS uid (
                                data text PRIMARY KEY
                            ); """
    cur.execute(create_modified_table)
    sql = '''delete from uid'''
    cur.execute(sql)
    sql = '''INSERT INTO uid (data) VALUES(?)'''
    cur.execute(sql, (uid,))
    con.commit()
    con.close()
    requests.get(f'http://localhost:8000/push/{uid}')

def set_new_balance(db_amount,db_comment_bc,address):
    con = sqlite3.connect('./db/receipts.db')
    cur = con.cursor()
    sql = ''' UPDATE donations
              SET amount = ?,
                  date_time = ?,
                  comment_bc = ?
              WHERE donation_address = ?'''   
    cur.execute(sql, (db_amount,datetime.now(),db_comment_bc,address))
    con.commit()

def query_address(address):
    con = sqlite3.connect('./db/receipts.db')
    cur = con.cursor()
    create_receipts_table = """ CREATE TABLE IF NOT EXISTS donations (
                    email text,
                    amount integer default 0 not null,
                    fname text,
                    donation_address text PRIMARY KEY,
                    zipcode text,
                    address text,
                    date_time text,
                    refund_address text,
                    crypto_ticker text,
                    wish_id text,
                    comment text,
                    comment_name text,
                    amount_expected integer default 0 not null,
                    consent text,
                    quantity integer default 0,
                    type text,
                    comment_bc integer default 0
                ); """

    cur.execute(create_receipts_table)
     
    cur.execute('SELECT * FROM donations WHERE donation_address = ?',[address])
    rows = cur.fetchall()
    pprint.pprint(cur.fetchall())
    return rows

def dump_json(wishlist):
    global json_fname
    lock = json_fname + ".lock"
    with FileLock(lock):
        #logit("Lock acquired.")
        with open(json_fname, 'w+') as f:
            json.dump(wishlist, f, indent=6,default=str)  

#checks if exists in DB (checking height was from an old script)
def checkHeight(tx_id,xmr_wow_node):
    con = sqlite3.connect('./db/xmr_ids.db')
    cur = con.cursor()
    create_tx_ids_table = """ CREATE TABLE IF NOT EXISTS txids (
                                id text PRIMARY KEY
                            ); """
    cur.execute(create_tx_ids_table)
    cur.execute('SELECT * FROM txids WHERE id = ?',[tx_id])
    rows = len(cur.fetchall())
    if rows == 0:
        logit("we dont exist")
        sql = ''' INSERT INTO txids(id)
                  VALUES(?) '''
        cur.execute(sql, (tx_id,))
        con.commit()
        #continue ..
    else:
        logit("we already exist in the db")
        con.commit()
        cur.close()
        return False
    con.commit()
    cur.close()
    #loop incase rpc daemon has not started up yet.
    retries = 0
    while True:
        try:
            logit(f"Trying to download from rpc {xmr_wow_node}")
            rpc_connection = AuthServiceProxy(service_url=xmr_wow_node)
            logit("after rpc con")
            logit(tx_id)
            params = {
                      "account_index":0,
                      "in":True
                     }
            #info = rpc_connection.get_transfers(params)
            #pprint.pprint(info)
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
            print(e)
            if retries > 10:
                logit("error: monero rpc connection failed")
                break
            else:
                logit("Retrying connection in 5 seconds")
                #logit("Retrying connection in 5 seconds.")
                time.sleep(5)
    if len(info['transfers']) == 1:
        return info["transfer"]
    else:
        for x in info["transfers"]:
            main(x,1)
            time.sleep(1)

def logit(text):
    with open("get_logged.txt", "a+") as f:
        f.write("[DEBUG]" + text)
        f.write("\n")
    print(text)


def formatAmount(amount,units):
    """decode cryptonote amount format to user friendly format.
    Based on C++ code:
    https://github.com/monero-project/bitmonero/blob/master/src/cryptonote_core/cryptonote_format_utils.cpp#L751
    """
    CRYPTONOTE_DISPLAY_DECIMAL_POINT = int(units)
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
    print(f"length of args = {len(sys.argv)}")
    if len(sys.argv) > 2:
        main(tx_id,0,"WOW")
    else:
        main(tx_id)

#apt-get install sqlite3 && \
#sqlite3 db/receipts.db 'update donations set amount = 0 where donation_address = "qpjnsuvyu9vmaetytr9qr7q724sx38lwn5p0dck3hk"'
#updateDatabaseJson("qpjnsuvyu9vmaetytr9qr7q724sx38lwn5p0dck3hk",0,"bch",data_wishlist,0.1)
