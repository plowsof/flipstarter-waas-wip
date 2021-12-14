from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import pprint 
import json
import os
import pickle
from filelock import FileLock
from datetime import datetime
import requests
from github import Github

import random
import string

import configparser

#Node will be taken from config file, hardcoded here for testing
node_url =  'http://eeebox:18085/json_rpc'

letters = string.ascii_lowercase
uid = ''.join(random.choice(letters) for i in range(10)) 

#This file is run once to host the http server
#values taken from a config file once

bch_path = ""
btc_path = ""

status = "123"

confirmed = 0
unconfirmed_balance = 0

btc_wishlist = {}

def getJson(config,fname):
    with open(fname,"r") as f:
        return json.load(f)


class S(BaseHTTPRequestHandler):
    global bch_path, btc_path
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
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
        thejson = json.loads(post_data)
        address = thejson["address"].replace("\n","")
        if thejson["status"]: #!= status:
            #is it a btc or bch address?
            if thejson["symbol"] == "bch":
                print(f"daemon_path= {bch_path}")
                daemon_path = bch_path
                print("BCH address status change")
                json_fname = "wishlist-data-bch.json"
                btc_wishlist = getJson(config,json_fname)
            else:
                daemon_path = btc_path
                print("BTC address status change")
                json_fname = "wishlist-data-btc.json"
                btc_wishlist = getJson(config,json_fname)

            status = thejson["status"]
            print(f"daemon_path: {daemon_path}")
            stream = os.popen(f"{daemon_path} getaddressbalance {address} --testnet")
            json_output = stream.read().replace("\n","")
            print(repr(json_output))
            output = json.loads(json_output)
            print(btc_wishlist)
            address_con = output["confirmed"]
            address_unc = output["unconfirmed"]
            print(f"conf {address_con}, unc {address_unc}")

            now_balance = float(address_unc) + float(address_con)
            for i in range(len(btc_wishlist["addresses"])):
                print(f"is {btc_wishlist['addresses'][i]['address']} == {address}:")
                if btc_wishlist["addresses"][i]["address"] == address:

                    old_balance = float(btc_wishlist["addresses"][i]["unconfirmed"]) + float(btc_wishlist["addresses"][i]["confirmed"])
                    if old_balance < now_balance:
                        #print(f"old balance: {old_balance} new balance : {now_balance}")
                        amount = float(now_balance) - float(old_balance)
                        btc_wishlist["addresses"][i]["unconfirmed"] = address_unc
                        btc_wishlist["addresses"][i]["confirmed"] = address_con
                        #print(f"This address: {address} received this many sats:{amount}")
                        btc_wishlist["metadata"]["date_modified"] = str(datetime.now())
                        #add to address history
                        tx_info = {
                        "amount":amount, 
                        "date_time":str(datetime.now())
                        }
                        btc_wishlist["addresses"][i]["history"].append(tx_info)
                        btc_wishlist["addresses"][i]["contributors"] += 1
                        pprint.pprint(btc_wishlist)
                        lock = FileLock(f"{json_fname}.lock")
                        with lock:
                            with open(json_fname, "w+") as f:
                                    json.dump(btc_wishlist, f, indent = 2)
                        
                        #end the loop early
                        num = i
                        i = len(btc_wishlist["addresses"]) + 1
            #JS will add these 2 for the total. we only cared about the amount for the history.
            #btc_wishlist["addresses"][i]["confirmed"] = address_con

def run(server_class=HTTPServer, handler_class=S, port=8080, config=[]):
    #load some json stuff
    global btc_totals, confirmed, btc_wishlist
    global bch_path, btc_path
    bch_path = config["bch"]["bin"]
    btc_path = config["btc"]["bin"]
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