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

def updateDatabaseJson(find_address,in_amount,ticker,saved_wishlist,bit_balance=0):
    now = int(time.time())
    db_wish_id = ""
    found = 0
    if ticker == "bch" or ticker == "btc":
        #bit_balance = balance now for this address
        #old balance = amount in database for this address
        rows = query_address(find_address)
        if len(rows) == 0:
            old_balance = 0
            in_amount = float(bit_balance)
        else:
            old_balance = rows[0][1]
            in_amount = float(bit_balance) - float(old_balance)
        print(f"oldbalance = {old_balance}")
        if old_balance >= bit_balance:
            return
        if in_amount < 0:
            print("[DEBUG]: in_amount negative****************")
            return
    for i in range(len(saved_wishlist["wishlist"])):
        if saved_wishlist["wishlist"][i][f"{ticker}_address"] == find_address:
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
            db_comment = ""
            db_comment_name = ""
            db_date_time = now
            db_ticker = ticker
            db_amount = in_amount
            db_wish_id = saved_wishlist["wishlist"][i]["title"]
            #Percent calculated by JS - or some timed script to periodically check         
            break
    if found == 0:
        address = find_address
        #rows is already set if bch/btc
        if ticker != "bch" and ticker != "btc":
            rows = query_address(address)
        #its a new address. continue
        if len(rows) == 0:
            #this metadata is useless - should remove -todo
            saved_wishlist["metadata"][f"{ticker}_total"] += float(in_amount)
            saved_wishlist["metadata"]["contributors"] += 1
        else:
            db_comment_bc = rows[0][16]
            db_comment = rows[0][10]

            if db_comment_bc == 0 and db_comment != "":
                db_comment_bc = 1
            else:
                db_comment = ""

            db_amount = float(rows[0][1])
            #bad variable names - this is == total(amount) += in_amount 
            db_amount += float(in_amount)
            con = sqlite3.connect('./db/receipts.db')
            cur = con.cursor()
            sql = ''' UPDATE donations
                      SET amount = ?,
                          date_time = ?,
                          comment_bc = ?
                      WHERE donation_address = ?'''   
            cur.execute(sql, (db_amount,datetime.now(),db_comment_bc,address))
            con.commit()
            #address exists in the receipt db
            db_email = rows[0][0]
            db_fname = rows[0][2]
            db_crypto_addr = rows[0][3]
            db_zip = rows[0][4]
            db_address = rows[0][5]
            db_date_time = now #is this a column in the db already?
            db_refund_addr = rows[0][7]
            db_ticker = rows[0][8]
            db_wish_id = rows[0][9]
            db_comment_name = rows[0][11]
            db_amount_expected = rows[0][12]
            db_consent = rows[0][13]
            db_quantity = rows[0][14]
            db_type = rows[0][15]
            print(f"We are looking for wish id {db_wish_id}")
            found = 0
            
            #we need db_wish_id -> wish title
            for i in range(len(saved_wishlist["wishlist"])):
                #logit(saved_wishlist[i])
                if saved_wishlist["wishlist"][i]["id"] == db_wish_id:
                    found = 1
                    #logit("we found the wish id -> title")
                    db_wish_id = saved_wishlist["wishlist"][i]["title"]
                    saved_wishlist["metadata"]["modified"] = now
                    #db_set_time_wish(int(time.time()))
                    saved_wishlist["wishlist"][i]["modified_date"] = now
                    saved_wishlist["wishlist"][i]["contributors"] += 1
                    saved_wishlist["wishlist"][i][f"{ticker}_total"] += float(in_amount)
                    history_tx = {
                    "amount":float(in_amount),
                    "date_time": now
                    }
                    saved_wishlist["wishlist"][i][f"{ticker}_history"].append(history_tx)   
                    break

            if found == 0:
                #weird, maybe the wish was put into the archive before being deleted
                print("Didnt find wish id")
                db_wish_id = "An already funded wish"
            #add to the total / history of that wish
            #send an email / or start a 20~ min timer to check?

    else:
        #dont need to sort if it was added to total
        #percent is not being set atm ~?
        #saved_wishlist["wishlist"] = sorted(saved_wishlist["wishlist"], key=lambda k: k['percent'],reverse=True)
        saved_wishlist["metadata"]["modified"] = now
        #db_set_time_wish(int(time.time()))
    if found == 1:
        #this is just a global history
        print(f"the comment = {db_comment}")
        comment = {
        "comment": db_comment,
        "comment_name": db_comment_name,
        "date_time": now,
        "usd_value": "",
        "ticker": db_ticker,
        "amount": in_amount,
        "id": db_wish_id
        }
        saved_wishlist["comments"]["comments"].append(comment)
        saved_wishlist["comments"]["modified"] = int(time.time())
        #db_set_time_comment(int(time.time()))
        
    else:
        print("this address is unknown.. but still its probably crypto ++")

    dump_json(saved_wishlist)
    static_main(config)
    uid = uuid.uuid4().hex
    asyncio.run(ws_work_around(uid))

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