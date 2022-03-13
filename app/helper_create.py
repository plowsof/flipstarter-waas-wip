from rss_feed import add_to_rfeed
import requests
import pprint
import os
import json
import configparser
import datetime
import sqlite3
import qrcode 
from PIL import Image
import threading
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
from colorama import Fore, Back, Style
import time
from datetime import datetime
from filelock import FileLock

def init_wishlist():
    #load wishlist from json file
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    viewkey = config["monero"]["viewkey"]
    main_address = config["monero"]["mainaddress"]
    thetime = datetime.now()
    total = {
        "xmr_total": 0,
        "btc_total": 0,
        "bch_total": 0,
        "contributors": 0,
        "modified": str(thetime),
        "title": "",
        "description": "",
        "image": "",
        "url": "",
        "viewkey": viewkey,
        "main_address": main_address,
        "status": "OK",
        "protocol": "v3",
    }
    the_wishlist = {}
    the_wishlist["wishlist"] = []
    the_wishlist["metadata"] = total
    the_wishlist["archive"] = []
    the_wishlist["comments"] = {}
    the_wishlist["comments"]["comments"] = []
    the_wishlist["comments"]["modified"] = 1
    #need a file lock on this (not if its init)
    with open("./static/data/wishlist-data.json", "w+") as f:
        json.dump(the_wishlist,f, indent=4) 

def wish_add(wish,config):
    local_ip = "localhost"
    try:
        new_wish = {
        "goal_usd": wish["goal"],
        "hours": "",
        "title": wish["title"],
        "description":wish["desc"],
        "bch_address":"",
        "btc_address":"",
        "xmr_address":"",
        "type": "gift"
        }
        add_to_rfeed(new_wish)
        bchuser = config["bch"]["rpcuser"]
        bchpass = config["bch"]["rpcpassword"]
        bchport = config["bch"]["rpcport"]
        btcuser = config["btc"]["rpcuser"]
        btcpass = config["btc"]["rpcpassword"]
        btcport = config["btc"]["rpcport"]
        if not is_bit_online(bchuser,bchpass,bchport):
            print("Bch daemon offline")
            return
        new_wish["bch_address"] = get_unused_address(config,"bch")
        put_qr_code(new_wish["bch_address"], "bch")
        if not is_bit_online(btcuser,btcpass,btcport):
            print("Btc daemon offline")
            return
        new_wish["btc_address"] = get_unused_address(config,"btc")
        put_qr_code(new_wish["btc_address"], "btc")
        rpc_port = config["monero"]["daemon_port"]
        if rpc_port == "":
            rpc_port = 18082
        rpc_url = "http://" + str(local_ip) + ":" + str(rpc_port) + "/json_rpc"
        wallet_path = os.path.basename(config['monero']['wallet_file'])
        retries = 0
        while True:
            if monero_rpc_online(rpc_url):
                break
            else:
                print_err("Waiting for Monero daemon to come online")
                if retries == 7:
                    print_err("Monero not online after 40 seconds")
                    sys.exit(1)
                time.sleep(10)
                retries += 1
        new_wish["xmr_address"] = get_unused_address(config,"xmr")
        
        #insert the addresses into the database
        wish_id = new_wish["xmr_address"][0:12]
        pre_receipts_add(new_wish["xmr_address"],"xmr",wish_id)
        pre_receipts_add(new_wish["bch_address"],"bch",wish_id)
        pre_receipts_add(new_wish["btc_address"],"btc",wish_id)
        put_qr_code(new_wish["xmr_address"], "xmr")


        orig_goal = wish["goal"]
        percent = int(config["wishlist"]["percent_buffer"]) / 100
        percent = float(percent) * int(orig_goal)
        goal = int(orig_goal) + int(percent)

        new_wish = { 
                    "goal_usd":int(wish["goal"]), #these will be in usd
                    "usd_total":0, #usd - if you cash out for stability
                    "contributors":0,
                    "status": "", #e.g. WIP / RELEASED
                    "description": wish["desc"],
                    "percent": 0,
                    "hours": 0, # $/h
                    "type": "gift",
                    "created_date": str(datetime.now()),
                    "modified_date": str(datetime.now()),
                    "author_name": "",
                    "author_email": "",
                    "id": new_wish["xmr_address"][0:12],
                    "qr_img_url_xmr": f"static/images/{new_wish['xmr_address'][0:12]}.png",
                    "qr_img_url_btc": f"static/images/{new_wish['btc_address'][0:12]}.png",
                    "qr_img_url_bch": f"static/images/{new_wish['bch_address'][0:12]}.png",
                    "title": wish["title"],
                    "btc_address": new_wish["btc_address"],
                    "bch_address": ("bchtest:" + new_wish["bch_address"]),
                    "xmr_address": new_wish["xmr_address"],
                    "btc_total": 0,
                    "xmr_total": 0,
                    "bch_total": 0,
                    "hour_goal": 0,
                    "xmr_history": [],
                    "bch_history": [],
                    "btc_history": [],
                    "btc_confirmed": 0,
                    "btc_unconfirmed": 0,
                    "bch_confirmed": 0,
                    "bch_unconfirmed": 0
        } 

        with open('./static/data/wishlist-data.json', "r") as f:
            now_wishlist = json.load(f)
        new_wish = new_wish.copy()
        now_wishlist["wishlist"].append(new_wish)
        data_json = "./static/data/wishlist-data.json"
        lock = FileLock(f"{data_json}.lock")
        with lock:
            with open(data_json, "w+") as f:
                json.dump(now_wishlist, f, indent=2) 
        pass
    except Exception as e:
        raise e

def bit_online(rpcuser,rpcpass,rpcport):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    payload = {
        "method": "getbalance",
        "params": [],
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    try:
        returnme = requests.post(url, json=payload).json()
        pprint.pprint(returnme)
        print("it worked")
        return True
    except Exception as e:
        print(e)
        print("it didnt worked")
        return False

def put_qr_code(address, xmr_btc):
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    www_root = config["wishlist"]["www_root"]
    if xmr_btc == "xmr":
        uri = "monero"
        logo = "xmr.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=4,
    )
    elif xmr_btc == "btc":
        uri = "bitcoin"
        logo = "btc.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=7,
        border=4,
    )
    else:
        uri = "bchtest"
        
        logo = "bch.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=7,
        border=4,
    )
    try:
        if not os.path.isdir(os.path.join(www_root,'images')):
            os.mkdir(os.path.join(www_root,"images"))
        pass
    except Exception as e:
        raise e

    title = address[0:12]
    if os.path.isfile(os.path.join(www_root,"images",f"{title}.png")):
        #dont bother recreating the qr image
        #could cause issues if you want to do that though
        return

    data = f"{uri}:{address}"
    qr.add_data(data)
    qr.make(fit=True)
    #img = qr.make_image(fill_color="black", back_color=(62,62,62))
    img = qr.make_image(fill_color=(62,62,62), back_color="white")
    img.save(os.path.join(www_root,"images",f"{title}.png"))
    f_logo = os.path.join(www_root,"images",logo)
    logo = Image.open(f_logo)
    logo = logo.convert("RGBA")
    im = Image.open(os.path.join(www_root,"images",f"{title}.png"))
    im = im.convert("RGBA")
    logo.thumbnail(thumnail)
    im.paste(logo,box=(142,142),mask=logo)
    #im.show()
    im.save(os.path.join(www_root,"images",f"{title}.png"))


def wish_prompt(config):
    wish={}
    reality = 0
    while True:
        try:
            wish["title"]
            pass
        except Exception as e:
            wish["title"] = str(input('Wish Title:'))
        try:
            wish["desc"]
            pass
        except Exception as e:
            wish["desc"] = input('Wish Description:')
        
        wish["goal"] = input('USD Goal:')
        try:
            int(wish["goal"])
            print("we should break now")
            reality = 1
            break
        except Exception as e:
            print(e)

        if reality == 1:
            break
    wish_add(wish,config)

    add = input('Add another wish y/n:')
    if 'y' in add.lower():
        wish={}
        wish_prompt(config)

def bit_online(rpcuser,rpcpass,rpcport):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    payload = {
        "method": "getbalance",
        "params": [],
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    try:
        returnme = requests.post(url, json=payload).json()
        pprint.pprint(returnme)
        print("it worked")
        return True
    except Exception as e:
        print(e)
        print("it didnt worked")
        return False

def pre_receipts_add(address,ticker,wish_id):
    db_data = {
    "email": "",
    #the amount selected by the form is meaningless
    #we only care about what gets deposited at the end
    #"amount": null_if_not_exists(vals,b"amount"),
    "amount": 0,
    "fname": "",
    "donation_address": address,
    "zipcode": "",
    "address": "",
    "date_time": datetime.now(),
    "refund_address": "",
    "crypto_ticker": ticker,
    "wish_id": wish_id,
    "comment": "",
    "comment_name": "",
    "amount_expected": 0,
    "consent":"",
    "quantity":0,
    "type": wish_id
    }
    db_receipts_add(db_data)

def db_receipts_add(data):
    con = sqlite3.connect('./db/receipts.db')
    cur = con.cursor()
    sql = ''' INSERT INTO donations (email,amount,fname,donation_address,zipcode,address,date_time,refund_address,crypto_ticker,wish_id,comment,comment_name,amount_expected,consent,quantity,type)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur.execute(sql, (data["email"],data["amount"],data["fname"],data["donation_address"],data["zipcode"],data["address"],data["date_time"],data["refund_address"],data["crypto_ticker"],data["wish_id"],data["comment"],data["comment_name"],data["amount_expected"],data["consent"],data["quantity"],data["type"]))
    con.commit()

def get_xmr_subaddress(rpc_url,wallet_file,title):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    xmr_wallet = os.path.basename(wallet_file)
    #they must check if the address exists in the receipts DB already / add it there
    #label could be added
    params={
            "account_index":0,
            "label": title
            }
    try:
        info = rpc_connection.create_address(params)
        return info["address"]
        pass
    except Exception as e:
        print("Error: Your monero node is offline. Ensure that start_daemons.py is running")
        sys.exit(1)


def btc_curl_address(wallet,rpcuser,rpcpass,rpcport):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    print("btc_curl_address")
    print(url)
    payload = {
        "method": "createnewaddress",
        "params": {
        "wallet": wallet
        },
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    returnme = requests.post(url, json=payload).json()
    try:
        pprint.pprint(returnme)
        if len(returnme['result']) > 30:
            return returnme['result']
        else:
            return False
    except Exception as e:
        return False

#notify twice removes the notify, not good
def address_create_notify(bin_dir,wallet_path,port,addr,create,notify,rpcuser,rpcpass,rpcport):
    local_ip = "localhost"
    port = "http://" + str(local_ip) + ":" + str(port)
    if create == 1:
        if "electrum" in bin_dir:
            address = btc_curl_address(wallet_path,rpcuser,rpcpass,rpcport)
        else:
            address = curl_address(rpcuser,rpcpass,rpcport)
    if notify == 1:
        if addr != "":
            address = addr
        if "Error" not in address:
            th = threading.Thread(target=rpc_notify,args=(rpcuser,rpcpass,rpcport,address,port,))
            th.start()
    return(address)

def rpc_notify(rpcuser,rpcpass,rpcport,address,callback):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    payload = {
        "method": "notify",
        "params": {
        "address": address,
        "URL": callback
        },
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    returnme = requests.post(url, json=payload).json()

#if result not a string > x chars
def curl_address(rpcuser,rpcpass,rpcport):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    payload = {
        "method": "createnewaddress",
        "params": [],
        "jsonrpc": "2.0",
        "id": "curltext",
    }
    returnme = requests.post(url, json=payload).json()
    try:
        if len(returnme['result']) > 30:
            return returnme['result']
        else:
            return false
    except Exception as e:
        return False

def get_unused_address(config,ticker,title=None):
    local_ip = "localhost"
    counter = 1
    while True:
        if ticker == "xmr":
            rpc_port = config["monero"]["daemon_port"]
            rpc_url = "http://" + str(local_ip) + ":" + str(rpc_port) + "/json_rpc"
            wallet_path = os.path.basename(config["monero"]["wallet_file"])
            address = get_xmr_subaddress(rpc_url,wallet_path,title)
            valid_coin = 1
            #notify qzr3duvhlknh9we5g8x3wvkj5qvh625tzv36ye9kwl http://127.0.1.1--testnet
        else:
            wallet_path = config[ticker]["wallet_file"]
            bin_dir = config[ticker]["bin"]
            port = config["callback"]["port"]
            rpcuser = config[ticker]["rpcuser"]
            rpcpass = config[ticker]["rpcpassword"]
            rpcport = config[ticker]["rpcport"]
            #bin_dir,wallet_path,port,addr,create,notify,rpcuser,rpcpass,rpcport
            #create address - check if unused - then create a notify
            address = address_create_notify(bin_dir,wallet_path,port,"",1,1,rpcuser,rpcpass,rpcport)
        if not address:
            break
        if "not" in address:
            continue
        if "Error" in address:
            continue
        print(f"Checking address: {address}")
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
                                    consent integer default 0,
                                    quantity integer default 0,
                                    type text,
                                    comment_bc integer default 0
                                ); """

        cur.execute(create_receipts_table)
        con.commit()
        cur.execute('SELECT * FROM donations WHERE donation_address = ?',[address])
        rows = len(cur.fetchall())
        #its a used address. continue loop
        if rows == 0:
            if ticker != "xmr":
                th = threading.Thread(target=rpc_notify,args=(rpcuser,rpcpass,rpcport,address,port,))
                th.start()
            break
        counter += 1
        if counter == 20:
            print(f"broken address = {address}")
            address = False
            break
    return address

def is_bit_online(rpcuser,rpcpass,rpcport):
    retries=0
    while True:
        if bit_online(rpcuser,rpcpass,rpcport):
            break
        else:
            print_err("Waiting for BCH/BTC daemon to come online")
            if retries == 7:
                print_err("BCH/BTC not online after 40 seconds")
                sys.exit(1)
            time.sleep(10)
            retries += 1
    #broken out of the loop / nodes is online
    return True

def print_msg(text):
    msg = f"{Fore.GREEN}> {Fore.WHITE}{text}"
    print(msg)

def print_err(text):
    msg = f"{Fore.RED}> {text}"

def monero_rpc_online(rpc_url):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.get_version()
        return True
    except Exception as e:
        return False
