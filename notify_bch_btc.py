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
        if thejson["status"]: #!= status:
            #is it a btc or bch address?
            if thejson["symbol"] == "bch":
                print(f"daemon_path= {bch_path}")
                daemon_path = bch_path
                print("BCH address status change")
            else:
                daemon_path = btc_path
                print("BTC address status change")
            ticker = thejson["symbol"]
            ticker_address = f"{ticker}_address"
            ticker_total = f"{ticker}_total"
            ticker_history = f"{ticker}_history"
            ticker_con = f"{ticker}_confirmed"
            ticker_unc = f"{ticker}_unconfirmed"
            status = thejson["status"]
            print(f"daemon_path: {daemon_path}")
            stream = os.popen(f"{daemon_path} getaddressbalance {address} --testnet")
            json_output = stream.read().replace("\n","")
            print(repr(json_output))
            output = json.loads(json_output)
            address_con = output["confirmed"]
            address_unc = output["unconfirmed"]
            print(f"conf {address_con}, unc {address_unc}")

            now_balance = float(address_unc) + float(address_con)

            data_fname = os.path.join(www_root,"data","wishlist-data.json")
            with open(data_fname, "r") as f:
                data_wishlist = json.load(f)
            for i in range(len(data_wishlist["wishlist"])):
                wishlist_address = data_wishlist["wishlist"][i][ticker_address]
                if ":" in wishlist_address:
                    wishlist_address = wishlist_address.split(":")[1]
                print(f"is {wishlist_address} == {address}:")
                if  wishlist_address == address:
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