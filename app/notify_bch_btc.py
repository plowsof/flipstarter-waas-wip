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
from notify_xmr_vps_pi import updateDatabaseJson

#This file is run once to host the http server
#values taken from a config file once

bch_path = ""
btc_path = ""

btc_wishlist = {}

rpcinfo={}
rpcinfo["bch"] = {}
rpcinfo["btc"] = {}

def getJson(fname):
    with open(fname,"r") as f:
        return json.load(f)

class S(BaseHTTPRequestHandler):
    global bch_path, btc_path, www_root, rpcinfo
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
        #electrum - Bech32 type starting with bc1
        if address[0:1] == "q":
            print("This is a bch address")
            daemon_path = bch_path
            ticker = "bch"
        else:
            print("This is a bitcoin address")
            daemon_path = btc_path
            ticker = "btc"
        rpcpass = rpcinfo[ticker]["pass"]
        rpcport = rpcinfo[ticker]["port"]
        rpcuser = rpcinfo[ticker]["user"]
        #should be an rpc call todo
        output = rpc_balance(rpcuser,rpcpass,rpcport,address)
        address_con = output["result"]["confirmed"]
        address_unc = output["result"]["unconfirmed"]
        bit_balance = float(address_con) + float(address_unc)
        data_fname = "./static/data/wishlist-data.json"
        with open(data_fname, "r") as f:
            data_wishlist = json.load(f)
        updateDatabaseJson(address,0,ticker,data_wishlist,bit_balance,address_con,address_unc)

def rpc_balance(rpcuser,rpcpass,rpcport,address):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    print(url)
    payload = {
        "method": "getaddressbalance",
        "params": {
        "address": address
        },
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    returnme = requests.post(url, json=payload).json()
    return returnme


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
    config.read('./db/wishlist.ini')
    rpcinfo["bch"] = {
    "port": config["bch"]["rpcport"],
    "user": config["bch"]["rpcuser"],
    "pass": config["bch"]["rpcpassword"]
    }
    rpcinfo["btc"] = {
    "port": config["btc"]["rpcport"],
    "user": config["btc"]["rpcuser"],
    "pass": config["btc"]["rpcpassword"]
    }
    if len(argv) == 2:
        run(port=int(argv[1]),config=config)
    else:
        
        run(port=12346,config=config)