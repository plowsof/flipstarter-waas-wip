from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import pprint 
import json
import os
import pickle
from filelock import FileLock
from datetime import datetime
import requests

import random
import string

import configparser
import sqlite3
from main import send_email, ticket_send_email
#This file is run once to host the http server
#values taken from a config file once

bch_path = ""
btc_path = ""

status = "123"

confirmed = 0
unconfirmed_balance = 0

btc_wishlist = {}

www_root = ""

def getJson(fname):
    with open(fname,"r") as f:
        return json.load(f)

class S(BaseHTTPRequestHandler):
    global bch_path, btc_path, www_root
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))
    def do_POST(self):
        print("HOLUP?")
        global status
        global confirmed, unconfirmed_balance, btc_wishlist
        global bch_path, btc_path
        global www_root
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
        thejson = json.loads(post_data)
        address = thejson["address"].replace("\n","")

        if ":" in address:
            address = address.split(":")[1]
        if address[0:1] == "q":
            print("This is a bchtest address")
            daemon_path = bch_path
            ticker = "bch"
        else:
            print("This is a bitcoin testnet address")
            daemon_path = btc_path
            ticker = "btc"

        ticker_address = f"{ticker}_address"
        ticker_total = f"{ticker}_total"
        ticker_history = f"{ticker}_history"
        ticker_con = f"{ticker}_confirmed"
        ticker_unc = f"{ticker}_unconfirmed"
        status = thejson["status"]
        print(f"the status is :{status}")
        print(f"daemon_path: {daemon_path}")
        stream = os.popen(f"{daemon_path} getaddressbalance {address} --testnet")
        json_output = stream.read().replace("\n","")
        #print(repr(json_output))
        output = json.loads(json_output)
        address_con = output["confirmed"]
        address_unc = output["unconfirmed"]
        print(f"conf {address_con}, unc {address_unc}")

        now_balance = float(address_unc) + float(address_con)

        data_fname = os.path.join(www_root,"data","wishlist-data.json")
        with open(data_fname, "r") as f:
            data_wishlist = json.load(f)
        #we need to detect if address is on wishlist 
        #if not, check our kyc database
        found = 0
        for i in range(len(data_wishlist["wishlist"])):
            wishlist_address = data_wishlist["wishlist"][i][ticker_address]
            if ":" in wishlist_address:
                wishlist_address = wishlist_address.split(":")[1]
            print(f"is {wishlist_address} == {address}:")
            if  wishlist_address == address:
                found = 1
                print("yes")
                old_balance = float(data_wishlist["wishlist"][i][ticker_unc]) + float(data_wishlist["wishlist"][i][ticker_con])
                if old_balance < now_balance:
                    #print(f"old balance: {old_balance} new balance : {now_balance}")
                    amount = float(now_balance) - float(old_balance)
                    data_wishlist["wishlist"][i][ticker_con] = float(address_con)
                    data_wishlist["wishlist"][i][ticker_unc] = float(address_unc)
                    data_wishlist["wishlist"][i][ticker_total] = float(now_balance)
                    tx_info = {
                                "amount":amount, 
                                "date_time":str(datetime.now())
                              }
                    data_wishlist["wishlist"][i][ticker_history].append(tx_info)
                    data_wishlist["wishlist"][i]["contributors"] += 1
                    modified = str(datetime.now())
                    data_wishlist["metadata"]["modified"] = modified
                    lock = FileLock(f"{data_fname}.lock")
                    with lock:
                        with open(data_fname, "w+") as f:
                            json.dump(data_wishlist, f, indent=2) 
                
                #end the loop early
                break
            else:
                print("not equal")
        if found == 0:
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
            con.commit()
            print(f"select * from where address = {address}")
            cur.execute('SELECT * FROM donations WHERE donation_address = ?',[address])
            rows = cur.fetchall()
            pprint.pprint(cur.fetchall())
            now = datetime.now()
            #its a new address. continue
            if len(rows) == 0:
                print("not in receipts or list - add to 'total' todo")
                #print("this address doesnt even exist in receipts lol")
                #saved_wishlist["metadata"]["total"] += float(extra_xmr)
                #saved_wishlist["metadata"]["contributors"] += 1
            else:
                #address exists in the receipt db
                db_email = rows[0][0]
                db_amount = rows[0][1] 
                db_fname = rows[0][2]
                db_crypto_addr = rows[0][3]
                db_zip = rows[0][4]
                db_address = rows[0][5]
                db_date_time = now #is it in the db already?
                db_refund_addr = rows[0][7]
                db_ticker = rows[0][8]
                db_wish_id = rows[0][9]
                db_comment = rows[0][10]
                db_comment_name = rows[0][11]
                db_amount_expected = rows[0][12]
                db_consent = rows[0][13]
                db_quantity = rows[0][14]
                db_type = rows[0][15]
                 
                #address not found in wishlist.
                #is it in receipt db?
                print("We didnt find this address in our wishlist")
                old_balance = db_amount
                print(f"old balanace: {old_balance}\n now balance : {now_balance}")
                if float(now_balance) > float(old_balance):
                    amount = now_balance - old_balance
                    db_amount += amount
                else:
                    #probably has just got 1 confirmation
                    return
                amount += int(db_amount)
                sql = ''' UPDATE donations
                          SET amount = ?,
                              date_time = ?
                          WHERE donation_address = ?'''   
                cur.execute(sql, (amount,datetime.now(),address))
                con.commit()
                found = 0
                #we need db_wish_id -> wish title
                for i in range(len(data_wishlist["wishlist"])):
                    if data_wishlist["wishlist"][i]["id"] == db_wish_id:
                        found = 1
                        data_wishlist["wishlist"][i][ticker_total] += float(amount)
                        tx_info = {
                                    "amount":amount, 
                                    "date_time": now
                                  }
                        data_wishlist["wishlist"][i][ticker_history].append(tx_info)
                        data_wishlist["wishlist"][i]["contributors"] += 1
                        modified = now
                        data_wishlist["metadata"]["modified"] = modified
                        data_wishlist["wishlist"][i]["modified_date"] = modified
                        db_wish_id = data_wishlist["wishlist"][i]["title"]
                        #end the loop early
                        break
                if found == 0:
                    #weird, maybe the wish was put into the archive before being deleted
                    db_wish_id = "An already funded wish" #are we in the archive?
                #add to the total / history of that wish
                #send an email / or start a 20~ min timer to check?
                comment = {
                "comment": db_comment,
                "comment_name": db_comment_name,
                "date_time": db_date_time,
                "ticker": db_ticker,
                "amount": db_amount
                }
                data_wishlist["comments"]["comments"].append(comment)
                data_wishlist["comments"]["modified"] = now
                lock = FileLock(f"{data_fname}.lock")
                with lock:
                    with open(data_fname, "w+") as f:
                        json.dump(data_wishlist, f, indent=2,default=str) 
                print("Time to send an email")
                print(f"the amount we are expecting is {db_amount_expected}")
                if db_amount_expected == 0:
                    send_email(db_email,db_amount,db_fname,db_crypto_addr,db_zip,db_address,db_date_time,db_refund_addr,db_ticker,db_wish_id)
                else:
                    if amount >= db_amount_expected:
                        #they sent the correct amount
                        ticket_send_email(db_fname,db_email,db_ticker,db_date_time,db_amount,db_amount_expected,db_consent,db_crypto_addr,db_quantity,db_type,1)
                    else:
                        #they sent an incorrect amount
                        ticket_send_email(db_fname,db_email,db_ticker,db_date_time,db_amount,db_amount_expected,db_consent,db_crypto_addr,db_quantity,db_type,0)

def run(server_class=HTTPServer, handler_class=S, port=8080, config=[]):
    #load some json stuff
    global btc_totals, confirmed, btc_wishlist
    global bch_path, btc_path
    global www_root
    bch_path = config["bch"]["bin"]
    btc_path = config["btc"]["bin"]
    www_root = config["wishlist"]["www_root"]
    '''
    with open('wishlist-data-btc.json',"r") as f:
        btc_wishlist = json.load(f)

    btc_totals = btc_wishlist["addresses"]
    '''
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    #print(httpd)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv
    config = configparser.ConfigParser()
    config.read('wishlist.ini')

    if len(argv) == 2:
        run(port=int(argv[1]),config=config)
    else:
        
        run(port=12346,config=config)