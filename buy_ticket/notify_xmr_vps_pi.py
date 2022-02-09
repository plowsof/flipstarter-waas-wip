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

from main import send_email, ticket_send_email

#os.chdir(os.path.dirname(sys.argv[0]))

cryptocompare.cryptocompare._set_api_key_parameter("-")

wishlist = []
#node_url = 'http://eeebox:18084/json_rpc'
config = configparser.ConfigParser()
config.read('wishlist.ini')
node_url = "http://localhost:" + config["monero"]["daemon_port"] + "/json_rpc"

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
    tx_data["amount"] = formatAmount(tx_data["amount"])
    found = 0
    main_fund = saved_wishlist["metadata"]["total"]
    for i in range(len(saved_wishlist["wishlist"])):
        try:
            if saved_wishlist["wishlist"][i]["xmr_address"] == tx_data["address"]:
                found = 1
                logit("we found the address in the list")
                saved_wishlist["wishlist"][i]["modified_date"] = str(datetime.now())
                saved_wishlist["metadata"]["modified"] = str(datetime.now())
                #contributor += 1 
                saved_wishlist["wishlist"][i]["contributors"] += 1
                #total += amount
                saved_wishlist["wishlist"][i]["xmr_total"] += float(tx_data["amount"])
                history_tx = {
                "amount":float(tx_data["amount"]),
                "date_time": str(datetime.now())
                }
                saved_wishlist["wishlist"][i]["xmr_history"].append(history_tx)
                #Percent calculated by JS - or some timed script to periodically check         
                break
        except Exception as e:
            raise e
    if found == 0:
        logit(f"We didnt find {tx_data['address']}this address in our wishlist")
        extra_xmr = float(tx_data["amount"])
        address = tx_data["address"]
        #donation received on invalid wishlist
        #Is this address in our 'kyc' database?
        #get some uid from db
        # uid (xmr address 1st x chars | email | address | amount)
        con = sqlite3.connect('receipts.db')
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
                        type text
                    ); """

        cur.execute(create_receipts_table)
         
        logit(f"select * from where address = {address}")
        cur.execute('SELECT * FROM donations WHERE donation_address = ?',[address])
        rows = cur.fetchall()
        pprint.pprint(cur.fetchall())
        #its a new address. continue
        if len(rows) == 0:
            logit("this address doesnt even exist in receipts lol")
            saved_wishlist["metadata"]["total"] += float(extra_xmr)
            saved_wishlist["metadata"]["contributors"] += 1
        else:
            db_amount = rows[0][1]
            extra_xmr += float(db_amount)
            logit("We exist in reciepts")
            sql = ''' UPDATE donations
                      SET amount = ?,
                          date_time = ?
                      WHERE donation_address = ?'''   
            cur.execute(sql, (extra_xmr,datetime.now(),address))
            con.commit()
            now = str(datetime.now())
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
            db_comment = rows[0][10]
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
                    saved_wishlist["wishlist"][i]["modified_date"] = now
                    saved_wishlist["wishlist"][i]["contributors"] += 1
                    saved_wishlist["wishlist"][i]["xmr_total"] += float(tx_data["amount"])
                    history_tx = {
                    "amount":float(tx_data["amount"]),
                    "date_time": now
                    }
                    saved_wishlist["wishlist"][i]["xmr_history"].append(history_tx)   
                    break

            if found == 0:
                #weird, maybe the wish was put into the archive before being deleted
                print("Didnt find wish id")
                db_wish_id = "An already funded wish"
            #add to the total / history of that wish
            #send an email / or start a 20~ min timer to check?
            logit("Time to send an email")
            print(f"expected: {db_amount_expected}")
            if db_amount_expected == 0:
                send_email(db_email,db_amount,db_fname,db_crypto_addr,db_zip,db_address,db_date_time,db_refund_addr,db_ticker,db_wish_id)
            else:
                if extra_xmr >= db_amount_expected:
                    #they sent the correct amount
                    ticket_send_email(db_fname,db_email,db_ticker,db_date_time,db_amount,db_amount_expected,db_consent,db_crypto_addr,db_quantity,db_type,1)
                else:
                    #they sent an incorrect amount
                    ticket_send_email(db_fname,db_email,db_ticker,db_date_time,db_amount,db_amount_expected,db_consent,db_crypto_addr,db_quantity,db_type,0)

    else:
        #dont need to sort if it was added to total
        saved_wishlist["wishlist"] = sorted(saved_wishlist["wishlist"], key=lambda k: k['percent'],reverse=True)
        modified = str(datetime.now())
        saved_wishlist["metadata"]["modified"] = modified
    comment = {
    "comment": db_comment,
    "comment_name": db_comment_name,
    "date_time": db_date_time,
    "ticker": db_ticker,
    "amount": db_amount
    }
    saved_wishlist["comments"]["comments"].append(comment)
    saved_wishlist["comments"]["modified"] = now
    dump_json(saved_wishlist)

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
    con = sqlite3.connect('xmr_ids.db')
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
