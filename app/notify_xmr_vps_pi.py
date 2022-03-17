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


#os.chdir(os.path.dirname(sys.argv[0]))

cryptocompare.cryptocompare._set_api_key_parameter("-")

wishlist = []
#node_url = 'http://eeebox:18084/json_rpc'
config = configparser.ConfigParser()
config.read('./db/wishlist.ini')
local_ip = "localhost"
node_url = "http://" + str(local_ip) + ":" + config["monero"]["daemon_port"] + "/json_rpc"

json_fname = os.path.join(config["wishlist"]['www_root'],"data","wishlist-data.json")



def getPrice(crypto,offset):
    data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
    #logit(f"[{crypto}]:{data[str(crypto)]['USD']}")
    value = float(data[str(crypto)]["USD"])
    #logit(f"value = {value}")
    return(float(value) - (float(value) * float(offset)))

def getJson():
    #must get the latest json as it may have been changed
    global json_fname
    with open(json_fname) as json_file:
        data = json.load(json_file)
        return data

def main(tx_id,multi=0):
    global json_fname, node_url
    logit(f"node_url = {node_url}")
    logit(f"json fname = {json_fname}")
    #check height
    #logit("Get json")
    saved_wishlist = getJson()
    #pprint.pprint(saved_wishlist)
    if multi == 0:
        #logit("multi = 0")
        tx_data = checkHeight(tx_id)
    else:
        tx_data = tx_id
    if not tx_data:
        return
    in_amount = formatAmount(tx_data["amount"])
    find_address = tx_data["address"]
    updateDatabaseJson(find_address,in_amount,"xmr",saved_wishlist)

def updateDatabaseJson(find_address,in_amount,ticker,saved_wishlist,bit_balance=0,bit_con=0,bit_unc=0):
    now = int(time.time())
    db_wish_id = ""
    found = 0
    for i in range(len(saved_wishlist["wishlist"])):
        if saved_wishlist["wishlist"][i][f"{ticker}_address"] == find_address:
            found = 1
            if ticker != "xmr":
                bit_balance = float(bit_con) + float(bit_unc)
                old_balance = float(saved_wishlist["wishlist"][i][f"{ticker}_unconfirmed"]) + float(saved_wishlist["wishlist"][i][f"{ticker}_confirmed"])
                if old_balance >= bit_balance:
                    return
                #print(f"old balance: {old_balance} new balance : {now_balance}")
                in_amount = float(bit_balance) - float(old_balance)
                saved_wishlist["wishlist"][i][f"{ticker}_confirmed"] = float(bit_con)
                saved_wishlist["wishlist"][i][f"{ticker}_unconfirmed"] = float(bit_unc)
            logit("we found the address in the list")
            saved_wishlist["wishlist"][i]["modified_date"] = now
            saved_wishlist["metadata"]["modified"] = now
            db_set_time_wish(int(time.time()))
            #contributor += 1 
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
        logit(f"We didnt find {find_address} this address in our wishlist")
        extra_xmr = float(in_amount)
        address = find_address
        #donation received on invalid wishlist
        #Is this address in our 'kyc' database?
        #get some uid from db
        # uid (xmr address 1st x chars | email | address | amount)
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
         
        logit(f"select * from where address = {address}")
        cur.execute('SELECT * FROM donations WHERE donation_address = ?',[address])
        rows = cur.fetchall()
        pprint.pprint(cur.fetchall())
        #its a new address. continue
        if len(rows) == 0:
            extra_xmr += float(bit_balance)
            logit("this address doesnt even exist in receipts lol")
            saved_wishlist["metadata"][f"{ticker}_total"] += float(extra_xmr)
            saved_wishlist["metadata"]["contributors"] += 1
        else:
            db_comment_bc = rows[0][16]
            db_comment = rows[0][10]

            if db_comment_bc == 0 and db_comment != "":
                db_comment_bc = 1
            else:
                db_comment = ""

            db_amount = rows[0][1]
            if ticker != "xmr":
                print(f"db_amount = {db_amount}\nbit_balance = {bit_balance}")
                if float(db_amount) == float(bit_balance):
                    return
                else:
                    print("amount(balance) in db != balance(now)")
                    in_amount = float(bit_balance) - float(db_amount)
                    print(f"in_amount = {in_amount}")
                    extra_xmr = float(bit_balance)
            extra_xmr += float(db_amount)
            logit("We exist in reciepts")
            sql = ''' UPDATE donations
                      SET amount = ?,
                          date_time = ?,
                          comment_bc = ?
                      WHERE donation_address = ?'''   
            cur.execute(sql, (extra_xmr,datetime.now(),db_comment_bc,address))
            con.commit()
            #address exists in the receipt db
            db_email = rows[0][0]
            db_amount = extra_xmr
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
                    logit("we found the wish id -> title")
                    db_wish_id = saved_wishlist["wishlist"][i]["title"]
                    saved_wishlist["metadata"]["modified"] = now
                    db_set_time_wish(int(time.time()))
                    saved_wishlist["wishlist"][i]["modified_date"] = now
                    saved_wishlist["wishlist"][i]["contributors"] += 1
                    saved_wishlist["wishlist"][i][f"{ticker}_total"] += float(in_amount)
                    if ticker != "xmr":
                        saved_wishlist["wishlist"][i][f"{ticker}_unconfirmed"] = bit_unc
                        saved_wishlist["wishlist"][i][f"{ticker}_confirmed"] = bit_con
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
        db_set_time_wish(int(time.time()))
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
        db_set_time_comment(int(time.time()))
        
    else:
        print("this address is unknown.. but still its probably crypto ++")

    dump_json(saved_wishlist)
    static_main(config)
def db_set_time_comment(time_stamp):
    con = sqlite3.connect('./db/modified.db')
    cur = con.cursor()
    create_modified_table = """ CREATE TABLE IF NOT EXISTS modified (
                                data integer default 0,
                                comment integer default 1,
                                wishlist integer default 1
                            ); """
    cur.execute(create_modified_table)
    sql = ''' UPDATE modified
              SET comment = ?
              WHERE data= ?'''   
    cur.execute(sql, (time_stamp,0))
    con.commit()
    con.close()

def db_set_time_wish(time_stamp):
    con = sqlite3.connect('./db/modified.db')
    cur = con.cursor()
    create_modified_table = """ CREATE TABLE IF NOT EXISTS modified (
                                data integer default 0,
                                comment integer default 1,
                                wishlist integer default 1
                            ); """
    cur.execute(create_modified_table)
    sql = ''' UPDATE modified
              SET wishlist = ?
              WHERE data= ?'''   
    cur.execute(sql, (time_stamp,0))
    con.commit()
    con.close()

def dump_json(wishlist):
    global json_fname
    lock = json_fname + ".lock"
    with FileLock(lock):
        #logit("Lock acquired.")
        with open(json_fname, 'w+') as f:
            json.dump(wishlist, f, indent=6,default=str)  

# should be check - exists in database first - then dont lockup from rpc
def checkHeight(tx_id):
    global node_url
    logit(node_url)
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
            logit(f"Trying to download from rpc {node_url}")
            rpc_connection = AuthServiceProxy(service_url=node_url)
            logit("after rpc con")
            logit(tx_id)
            params = {
                      "account_index":0,
                      "in":True
                     }
            info = rpc_connection.get_transfers(params)
            #pprint.pprint(info)
            params = {
                      "account_index":0,
                      "txid":tx_id
                     }
            info = rpc_connection.get_transfer_by_txid(params)
            #pprint.pprint(info)
            break
        except (requests.HTTPError,
          requests.ConnectionError,
          JSONRPCException) as e:
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
    #tx_id = "457c710fdae5dd8adbd9925044eb95b3617e3b66bf56ab16d0fb6a8b12f89509"
    main(tx_id)
