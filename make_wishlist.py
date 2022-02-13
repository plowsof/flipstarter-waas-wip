
import pprint
import json
from datetime import datetime
import qrcode 
from PIL import Image
import os
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
import time
import subprocess
import configparser
import sys
import random
import string
#import _thread as thread
import psutil
from start_daemons import start_btc_daemon, start_bch_daemon, find_working_node
import textwrap
from colorama import Fore, Back, Style
import shutil
import threading
import sqlite3 
import requests
#bitcoin - have to ./make_libsecp256k1.sh 

viewkey = ""
main_address = ""

#Api key of "-" appears to work currently, this may change,

#need to get these from the monero wallet - these are just placeholders for now
percent_buffer = 0.05
#include proxy_params;
#proxy_pass https://localhost:8000

wishes =[]
btc_info = []
bch_info = []
#wallet_path = "/home/human/.electrum/testnet/wallets/testnet"
wallet_path = "/home/human/freelance/wallets/testnet"
#electrum_path = "/electrum-4.1.5-x86_64.AppImage"
electrum_path = "/bin/Electrum-4.1.5/run_electrum"
http_server = "http://localhost:1245"
#bitcoins json file will just be addresses + amount pairings for JS to link up
monero_wallet_rpc = "/bin/monero-wallet-rpc"

bch_wallet_file = ""
btc_wallet_file = ""

wallet_dir = os.path.join(os.path.abspath(os.path.join(os.getcwd(),"wallets")))


www_root = ""

#https://stackoverflow.com/questions/17455300/python-securely-remove-file
def secure_delete(path, passes=1):
    length = os.path.getsize(path)
    print(f"Wiping {path} with random data.")
    with open(path, "br+", buffering=-1) as f:
        for i in range(passes):
            f.seek(0)
            f.write(os.urandom(length))
            print(f"Pass {i}")
        f.close()
    print("Removing the file")
    os.remove(path)

def address_create_notify(bin_dir,wallet_path,port,addr,create,notify,rpcuser,rpcpass,rpcport):
    port = "http://localhost:" + str(port)
    print("address_create_notify")
    print(f'bin dir = {bin_dir}')
    print(f'walletpath = {wallet_path}')
    print(f'port:{port}')
    if create == 1:
        if "electrum" in bin_dir:
            thestring = f"./{bin_dir} createnewaddress -w {wallet_path} --offline --testnet "
            print(f'cmd : {thestring}')
            stream = os.popen(thestring)
            output = stream.read()
            #that was fun. address had a newline on it.
            address = output.replace("\n","")
        else:
            address = curl_address(rpcuser,rpcpass,rpcport)
    if notify == 1:
        if addr != "":
            address = addr
        th = threading.Thread(target=thread_notify,args=(bin_dir,address,port,))
        th.start()
    return(address)

def thread_notify(bin_dir,address,port):
    thestring = f"./{bin_dir} notify {address} {port} --testnet"
    print(thestring)
    stream = os.popen(thestring)
    output = stream.read()
    print(output)

def curl_address(rpcuser,rpcpass,rpcport):
    url = f"http://{rpcuser}:{rpcpass}@localhost:{rpcport}"
    print(url)
    payload = {
        "method": "createnewaddress",
        "params": [],
        "jsonrpc": "2.0",
        "id": 0,
    }
    returnme = requests.post(url, json=payload).json()
    pprint.pprint(returnme)
    return returnme["result"] 


def get_xmr_subaddress(rpc_url,wallet_file,title):
    print(f"[DEBUG] : rpc url : {rpc_url}")
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    xmr_wallet = os.path.basename(wallet_file)
    print(f"xmr wallet file: {xmr_wallet}")
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

def get_unused_address(config,ticker,title=None):
    while True:
        if ticker == "xmr":
            rpc_port = config["monero"]["daemon_port"]
            rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
            wallet_path = os.path.basename(config["monero"]["wallet_file"])
            address = get_xmr_subaddress(rpc_url,wallet_path,title)
            valid_coin = 1
            #notify qzr3duvhlknh9we5g8x3wvkj5qvh625tzv36ye9kwl http://localhost:12347 --testnet
            print(f"the address is: {address}")

        if ticker == "bch" or ticker == "btc":
            wallet_path = config[ticker]["wallet_file"]
            bin_dir = config[ticker]["bin"]
            port = config["callback"]["port"]
            rpcuser = config[ticker]["rpcuser"]
            rpcpass = config[ticker]["rpcpassword"]
            rpcport = config[ticker]["rpcport"]
            address = address_create_notify(bin_dir,wallet_path,port,"",1,1,rpcuser,rpcpass,rpcport)
        if "not" in address:
            continue
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
                                    consent integer default 0,
                                    quantity integer default 0,
                                    type text,
                                    comment_bc integer default 0
                                ); """

        cur.execute(create_receipts_table)
        con.commit()
        cur.execute('SELECT * FROM donations WHERE address = ?',[address])
        rows = len(cur.fetchall())
        pprint.pprint(cur.fetchall())
        #its a used address. continue loop
        if rows == 0:
            break
    return address

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

def put_qr_code(address, xmr_btc):
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
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
    print(f_logo)
    logo = Image.open(f_logo)
    logo = logo.convert("RGBA")
    print(logo.size)
    im = Image.open(os.path.join(www_root,"images",f"{title}.png"))
    im = im.convert("RGBA")
    logo.thumbnail(thumnail)
    im.paste(logo,box=(142,142),mask=logo)
    #im.show()
    im.save(os.path.join(www_root,"images",f"{title}.png"))

def dump_json(wishlist):
    global www_root
    with open(os.path.join(www_root,"data",'wishlist-data.json'), 'w+') as f:
        json.dump(wishlist, f, indent=6) 

#get input from a used wallet
def load_old_txs():
    #todo - update so this adds tx ids to the database
    global wishes
    rpc_connection = AuthServiceProxy(service_url=node_url)
    #label could be added
    params={
            "account_index":0,
            "in": True
            }
    old_txs = {}
    info = rpc_connection.get_transfers(params)
    num = 0

    if info["in"]:
        print("Wallet history detected. Searching for addresses in our list..")
        for tx in info["in"]:
            old_txs[num] = {tx["address"]: formatAmount(tx["amount"])}
            num += 1
        #pprint.pprint(old_txs)
        for wi in range(len(wishes)):
            for hi in range(len(old_txs)):
                #add, amount = old_txs[i]
                try:
                    if old_txs[hi][wishes[wi]["address"]]:
                        print(f"{wishes[wi]['address']} got +1 contributors and {old_txs[hi][wishes[wi]['address']]} XMR")
                        #pprint.pprint(wishes[wi])
                        wishes[wi]["contributors"] += 1
                        wishes[wi]["total"] += float(old_txs[hi][wishes[wi]["address"]])
                        wishes[wi]["percent"] = float(wishes[wi]["total"]) / float(wishes[wi]["goal"]) * 100  
                        #pprint.pprint(wishes[wi])
                except Exception as e:
                   continue
                

def create_new_wishlist():
    print("we're at create_new_wishli")
    #load wishlist from json file
    config = configparser.ConfigParser()
    config.read('wishlist.ini')

    viewkey = config["monero"]["viewkey"]
    main_address = config["monero"]["mainaddress"]
    percent_buffer = config["wishlist"]["percent_buffer"]
    www_root = config["wishlist"]["www_root"]

    with open("your_wishlist.json", "r") as f:
        wishlist = json.load(f)

    for wish in wishlist["wishlist"]:
        pprint.pprint(wish)
        goal = wish["goal_usd"]

        desc = wish["description"]
        address = wish["xmr_address"]
        btc_address = wish["btc_address"]
        bch_address = wish["bch_address"]
        hours = wish["hours"]
        w_type = wish["type"]
        title = wish["title"]

        usd_hour_goal = wish["hours"]
        if hours:
            goal += (float(usd_hour_goal) * float(percent_buffer)) 
            goal *= hours
        else:
            orig_goal = goal
            percent = int(percent_buffer) / 100
            percent = float(percent) * int(orig_goal)
            goal = int(goal) + int(percent)

        app_this = { 
                    "goal_usd":goal, #these will be in usd
                    "contributors":0,
                    "description": desc,
                    "percent": 0,
                    "hours": hours, # $/h
                    "type": w_type,
                    "status": "", #e.g. WIP / RELEASED
                    "created_date": str(datetime.now()),
                    "modified_date": str(datetime.now()),
                    "author_name": "",
                    "author_email": "",
                    "id": address[0:12],
                    "qr_img_url_xmr": f"flask/static/images/{address[0:12]}.png",
                    "qr_img_url_btc": f"flask/static/images/{btc_address[0:12]}.png",
                    "qr_img_url_bch": f"flask/static/images/{bch_address[0:12]}.png",
                    "title": title,
                    "btc_address": btc_address,
                    "bch_address": ("bchtest:" + bch_address),
                    "xmr_address": address,
                    "usd_total":0, #usd - if you cash out for stability
                    "btc_total": 0,
                    "xmr_total": 0,
                    "bch_total": 0,
                    "hour_goal": usd_hour_goal,
                    #could combine these into 1 'history' list with 'coin' set for each
                    "xmr_history": [],
                    "bch_history": [],
                    "btc_history": [],
                    "usd_history": [],
                    "btc_confirmed": 0,
                    "btc_unconfirmed": 0,
                    "bch_confirmed": 0,
                    "bch_unconfirmed": 0
        } 
        wishes.append(app_this)
        put_qr_code(address,"xmr")
        put_qr_code(btc_address,"btc")
        put_qr_code(bch_address,"bch")
    
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

    #search wallet for 'in' history, then compare addresses to our new list.
    #if matching address are found then contributors are +=1'd and amount+=amount.
    #monero-wallet-rpc daemon must be running ofcourse
    #load_old_txs()

    the_wishlist = {}
    the_wishlist["wishlist"] = wishes
    the_wishlist["metadata"] = total
    the_wishlist["archive"] = []
    the_wishlist["comments"] = {}
    the_wishlist["comments"]["comments"] = []
    the_wishlist["comments"]["modified"] = 1

    #need a file lock on this

    with open(os.path.join(www_root,"data","wishlist-data.json"), "w+") as f:
        json.dump(the_wishlist,f, indent=4) 


def start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,wallet_file,remote_node=None):
    global wallet_dir
    if wallet_file == None:
        rpc_args = [ 
            f".{rpc_bin_file}", 
            "--wallet-dir", wallet_dir,
            "--rpc-bind-port", rpc_port,
            "--disable-rpc-login", "--stagenet",
            "--daemon-address", remote_node
        ]
    else:
        print("wallet file was provided")
        rpc_args = [ 
            f".{rpc_bin_file}", 
            "--wallet-file", wallet_file,
            "--rpc-bind-port", rpc_port,
            "--disable-rpc-login", "--stagenet",
            "--daemon-address", remote_node,
            "--password", ""
        ]

    pprint.pprint(rpc_args)
    monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)

    kill_daemon = 0
    print("Starting Monero rpc...")
    for line in iter(monero_daemon.stdout.readline,''):
        #debug output
        #print(str(line.rstrip()))
        if b"Error" in line.rstrip() or b"Failed" in line.rstrip():
            kill_daemon = 1
            break
        if b"Starting wallet RPC server" in line.rstrip():
            print("Success!")
            rpc_connection = AuthServiceProxy(service_url=rpc_url)
            if wallet_file != None:
                http = ""
                if "http://" not in remote_node:
                    http = "http://"
                rpc_remote = http + remote_node + "/json_rpc"
                remote_rpc_connection = AuthServiceProxy(service_url=rpc_remote)
                data = remote_rpc_connection.get_info()
                info = rpc_connection.refresh({"start_height": (data['height'] - 1)})
                rpc_connection.store()
            break
        #time.sleep(1)
    if kill_daemon == 1:
        monero_daemon.terminate()
        sys.exit(1)

    num_retries = 0
    while True:
        try:
            info = rpc_connection.get_version()
            print("Monero RPC server online.")
            return monero_daemon
        except Exception as e:
            print("Trying again..")
            if num_retries > 30:
                #the lights are on but nobodys home, exit
                print("Unable to communiucate with monero rpc server. Exiting")
                sys.exit(1)
            time.sleep(5)
            num_retries += 1
    if wallet_file:
        #open this wallet
        info = rpc_connection.open_wallet({"filename": wallet_file, "password" :""})

def monero_rpc_online(rpc_url):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.get_version()
        return True
    except Exception as e:
        print("Offline as an error")
        return False

def monero_rpc_close_wallet(rpc_url):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.close_wallet()
        pprint.pprint(info)
        pass
    except Exception as e:
        print(e)
        sys.exit(1)

def create_monero_wallet(config):
    global wallet_dir, monero_wallet_rpc, rpc_bin_file
    rpc_port = config["monero"]["daemon_port"]
    if rpc_port == "":
        rpc_port = 18082
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
    print(rpc_url)
    if not os.path.isfile(os.path.join(".", "bin", "monero-wallet-rpc")):
        print("/bin/monero-wallet-rpc missing, unable to create monero walllet, quitting.")
        sys.exit(1)
    if monero_rpc_online(rpc_url) == True:
        print("rpc detected.. closing..")
        for proc in psutil.process_iter():
            # check whether the process name matches
            if "-rpc" in proc.name():
                proc.kill()
    #start the monero-rpc-wallet daemon
    print("start it up")
    list_remote_nodes = []
    fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

    remote_node = "http://" + str(find_working_node(list_remote_nodes))
    #remote_node = "http://stagenet.melo.tools:38081"
    letters = string.ascii_lowercase
    wallet_fname = "monero_" + ''.join(random.choice(letters) for i in range(10))
    wallet_path = os.path.join(wallet_dir,wallet_fname)
    rpc_remote = remote_node + "/json_rpc"
    remote_rpc_connection = AuthServiceProxy(service_url=rpc_remote)
    data = remote_rpc_connection.get_info()
    #--------------------------------------
    #  create hot wallet 
    #--------------------------------------
    auto_create = 0
    if prompt_wallet_create("xmr"):
        auto_create = 1
        print(monero_wallet_rpc)
        print(rpc_port)
        print(rpc_url)
        print(remote_node)
        monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,None,remote_node)
        print("Creating a Monero wallet..")
        #print(rpc_url)
        rpc_connection = AuthServiceProxy(service_url=rpc_url)
        #label could be added
        params={
                "filename": wallet_fname,
                "language": "English"
                }
        print(wallet_fname)
        info = rpc_connection.create_wallet(params)
        print("after create wallet")
        print("try and open the walleta")

        info = rpc_connection.open_wallet({"filename": wallet_fname,"password": ""})
        #to get block height data we need to use /json_rpc

        view_key = rpc_connection.query_key({"key_type": "view_key"})["key"]
        mnemonic = rpc_connection.query_key({"key_type": "mnemonic"})["key"]
        spend_key = rpc_connection.query_key({"key_type": "spend_key"})["key"]
        main_address = rpc_connection.get_address()["address"]
        config["monero"]["viewkey"] = view_key
        config["monero"]["mainaddress"] = main_address
        wrapper = textwrap.TextWrapper(width=100)
        
        wrapped_seed = wrapper.wrap(text=mnemonic)
        print(f"*************[{Style.BRIGHT}{Fore.RED}Monero {Style.RESET_ALL}Wallet]*************")
        print("*")
        print(f"Your Monero wallet seed is:") 
        for line in wrapped_seed:
            print(line)
        print("*")
        print(f"restore height: {data['height']}")
        print(f"main address: {main_address}")
        print(f"view key: {view_key}")
        print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
        print("*************[Monero Wallet]*************")
        #print(f"setting block height from remote node to: {data['height']}")

        input("Write your seed down on paper\n If you do not do this you will not be able to spend any money you get as this tool uses view-only wallets.\n Press Enter to continue >>")

        #print("closing hot wallet...")
        rpc_connection.close_wallet()
        #print("deleting hot wallet...")
        
        print("Secure deletion of wallet / keys file (3 passes of random data)...")
        keys = wallet_path + ".keys"
        address_file = wallet_path + ".address.txt"
        secure_delete(keys, passes=3)
        secure_delete(wallet_path, passes=3)
        os.remove(address_file)
        print("Monero hot wallet files deleted.")

        #print("quiting original  rpc process")
        monero_daemon.terminate()
        monero_daemon.communicate()
        for proc in psutil.process_iter():
            # check whether the process name matches
            if "monero-wallet-" in proc.name():
                #print(proc.name())
                proc.kill()
    else:
        #view_key
        #main_address
        key_data = prompt_monero_keys()
        view_key = key_data["view_key"]
        main_address = key_data["main_address"]
    #--------------------------------------
    #  restore from view key
    #--------------------------------------
    wallet_created = 0
    while True:
        wallet_json_data = {
            "version":1,
            "filename":wallet_path,
            "scan_from_height":data['height'],
            "password":"",
            "viewkey":view_key,
            "address":main_address
            }
        json_path = wallet_path + ".json"
        with open(json_path, "w+") as f:
            json.dump(wallet_json_data,f)

        #dummy wallet would be here TODO
        rpc_args = [ 
        f".{monero_wallet_rpc}",
        "--rpc-bind-port", rpc_port,
        "--disable-rpc-login", "--stagenet",
        "--daemon-address", remote_node,
        "--generate-from-json", json_path
        ]
        monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)
        print("Busy creating a view-only Monero wallet...")
        #wallet_rpc_server.cpp:4509 Error creating wallet: failed to parse view key secret key
        for line in iter(monero_daemon.stdout.readline,''):
            #debug output
            #print(str(line.rstrip()))
            if b"Error" in line.rstrip() or b"Failed" in line.rstrip():
                print("View-key / Main address incorrect , try again")
                key_data = prompt_monero_keys()
                view_key = key_data["view_key"]
                main_address = key_data["main_address"]
                break
            if os.path.isfile(wallet_path):
                wallet_created = 1
                break
        if wallet_created == 1:
            break
    
    print("View-only wallet created.")
    #remove the broken wallet file(??) (in testing i had to remove the wallet file for some reason)
    monero_daemon.terminate()
    monero_daemon.communicate()
    os.remove(wallet_path)
    #close it so we can set wallet dir(??)
    
    #start with the keys file only
    #special
    print("Loading view-only wallet...")
    list_remote_nodes = []
    fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

    remote_node = "http://" + str(find_working_node(list_remote_nodes))
    if remote_node:
        monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_path,remote_node)
    else:
        print("Error monero remote unreachable")
        return
    
    print("Loaded")

    #assuming we can still use the same port..
    print("Confirming view-only wallet is an exact copy of the hot-wallet")
    new_view_key = rpc_connection.query_key({"key_type": "view_key"})["key"]
    if new_view_key != view_key:
        print("Fatal error: new wallet does not match")
        sys.exit(1)
    else:
        print("View-only wallet is an exact copy of the (deleted) hot-wallet")
    #omiting the wallet-dir makes generate-from-json work (?)
    #but we need wallet-dir to use it
    #monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_fname,remote_node)
    print("Should be online now?")
    config["monero"]["wallet_file"] = wallet_path
    #TODO viewkey main_address in config file
    with open('wishlist.ini', 'w') as configfile:
        config.write(configfile)

    #delete variables from memory
    del data 
    del view_key 
    del mnemonic 
    del spend_key 
    del main_address 
    return monero_daemon

def prompt_wallet_create(ticker):
    if ticker == "bch":
        coin = "Bitcoin-Cash"
    elif ticker == "btc":
        coin = "Bitcoin"
    else:
        coin = "Monero"
    answer = ""
    print(f"No {coin} wallet detected. \n 1) Create one automatically. \n 2) Enter your own public view-key")
    while answer not in [1,2]:
        answer = int(input("enter 1 or 2 >> "))
    if answer == 1:
        return True
    else: 
        return False

def prompt_monero_keys():
    view_key = ""
    main_address = ""
    while view_key == "":
        view_key = input("Enter the Monero view-key >>")
    while main_address == "":
        main_address = input ("Enter the main wallet address >>")
    data = {
    "view_key": viewkey,
    "main_address": main_address
    }
    return data

def create_bit_wallet(config,bchbtc):
    global wallet_dir
    letters = string.ascii_lowercase
    if bchbtc == "btc":
        electron_bin = config["btc"]["bin"]
        find_me = "electrum-"
        c_colour = Fore.RED
        c_name = "Bitcoin"
        wallet_fname = "bitcoin_" + ''.join(random.choice(letters) for i in range(10)) 
        wallet_path = os.path.join(wallet_dir,wallet_fname)
        run_args = [
        electron_bin, "create", "-w", wallet_path, "--offline", "--testnet"
        ]
    else:
        electron_bin = config["bch"]["bin"]
        find_me = "Electron"
        c_colour = Fore.GREEN
        c_name = "Bitcoin Cash"
        wallet_fname = "cash_" + ''.join(random.choice(letters) for i in range(10)) 
        wallet_path = os.path.join(wallet_dir,wallet_fname)
        run_args = [
        electron_bin, "create", "-w", wallet_path, "--testnet"
        ]
    
    #python3 run_electrum create -w lol --offline
    for x in os.listdir("bin"):
        if find_me in x:
            electrum_bin = os.path.join("bin",x)
    if electron_bin == "":
        return False
    
    #print(wallet_path)
    #--------------------------------------
    #  create hot wallet
    #--------------------------------------
    if prompt_wallet_create(bchbtc):
        bch_bin = subprocess.Popen(run_args,stdout=subprocess.PIPE)
        #wait until finished
        bch_bin.communicate(input=b"\n")

        with open(wallet_path, "r") as f:
            bch_data = json.load(f)
        print(f"*************[{Style.BRIGHT}{c_colour}{c_name} {Style.RESET_ALL}wallet]*************")
        print(f"Your {c_name} wallet seed is:")
        print(f"{bch_data['keystore']['seed']}")
        print(f"format:{bch_data['keystore']['seed_type']} derivation: {bch_data['keystore']['derivation']}")
        print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
        print("*************[Bitcoin wallet]*************")
        input("Write your seed down on paper or you can never spend money you receive \n Press enter to continue >>")

        config[bchbtc]["wallet_file"] = wallet_path
        config[bchbtc]["xpub"] = bch_data['keystore']['xpub']
        with open('wishlist.ini', 'w') as configfile:
            config.write(configfile)
        #stop_bit_daemon(electrum_bin)

        secure_delete(wallet_path,passes=3)
    else:
        #ask for view keys
        # set the bch_data['keystore']['xpub']
        answer = input ("Paste your xpub key, then press enter\n>>")
        bch_data = { "keystore": { "xpub": answer
        }}
    #--------------------------------------
    #  create view-only
    #--------------------------------------
    run_args = [
    electron_bin, "restore", "-w", wallet_path, "--offline", "--testnet", bch_data['keystore']['xpub']
    ]
    bch_bin = subprocess.Popen(run_args,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    bch_bin.communicate()

    print("Verifying new view-key matches.")
    with open(wallet_path, "r") as f:
        json_data = json.load(f)
    orig_view_key = bch_data['keystore']['xpub']
    new_view_key = json_data['keystore']['xpub']
    if orig_view_key == new_view_key:
        print("New view-key is a match.")
    else:
        print("Fatal error: new wallet does not match the original")
        sys.exit(1)

    #del bch variables
    del bch_data
    del orig_view_key
    del new_view_key
    del json_data

    return config

#set viewkeys for wallets here
def main(config):
    global www_root
    www_root = config["wishlist"]["www_root"]
    rpc_port = config["monero"]["daemon_port"]
    if rpc_port == "":
        rpc_port = 18082
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
    #Error checks needed here on user inputs
    if not www_root:
        www_root = input('Where is your root website folder (e.g. /var/www/html):')
    www_data_dir = os.path.join(www_root,"data")
    www_qr_dir = os.path.join(www_root,"qrs")
    www_js_dir = os.path.join(www_root,"js")
    if not os.path.isdir(os.path.join(www_data_dir)):
        os.mkdir(www_data_dir)
    if not os.path.isdir(www_qr_dir):
        os.mkdir(www_qr_dir)
    if not os.path.isdir(www_js_dir):
        os.mkdir(www_js_dir)
    #Monero setup
    wallet_file = config["monero"]["wallet_file"]
    if not wallet_file:
        monero_online = 1
        print("No wallet provided. Creating one.")
        monero_daemon = create_monero_wallet(config)
    else:
        monero_online = 0
        if not os.path.isfile(config["monero"]["wallet_file"]):
            print("***********************************")
            print("Monero wallet missing! see wishlist.ini")
            print("***********************************")
            sys.exit(1)
        else:
            #a wallet file was supplied
            #we still need to start the rpc up
            list_remote_nodes = []
            fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
            for i in range(int(fallback_remote_nodes)):
                num = (i+1)
                list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

            remote_node = "http://" + str(find_working_node(list_remote_nodes))
            if remote_node:
                monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_file,remote_node)
            else:
                print("Error monero remote unreachable")
                return
            

    if not config["bch"]["wallet_file"]:
        #maybe we dont have to close the daemon in create wallet
        config = create_bit_wallet(config,"bch")
    else:
        if not os.path.isfile(config["bch"]["wallet_file"]):
            print("***********************************")
            print("BCH wallet missing! see wishlist.ini")
            print("***********************************")
            sys.exit(1)
    #start / open the BCH daemon / wallet
    print('Start the BCH daemon / open wallet')
    bch_wallet_path = config["bch"]["wallet_file"]
    electron_bin = config["bch"]["bin"]
    run_args = [
    electron_bin, "daemon", "load_wallet", "-w", bch_wallet_path, "--testnet"
    ]
    bch_daemon = subprocess.Popen(run_args, stdout=subprocess.PIPE)
    bch_daemon.communicate()
    

    if not config["btc"]["wallet_file"]:
        print("make a btc wallet")
        config = create_bit_wallet(config,"btc")
    else:
        if not os.path.isfile(config["btc"]["wallet_file"]):
            print("***********************************")
            print("BTC wallet missing! see wishlist.ini")
            print("***********************************")
            sys.exit(1)
    print('Start the BTC daemon / open wallet')
    

    rpcuser = config["bch"]["rpcuser"]
    rpcpass = config["bch"]["rpcpassword"]
    rpcport = config["bch"]["rpcport"]
    bch_wallet_path = config["bch"]["wallet_file"]
    #print(f"time to break: {btc_wallet_path} {electrum_bin}")

    rpc_port = config["monero"]["daemon_port"]
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"

    #create 'your_wishlist.json'
    print("Lets create your wishlist.")
    wish_prompt()
    with open('your_wishlist.json') as f:
            wishlist = json.load(f)

    #scan wishes and assign addresses if none given
    #get new saved variables
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    port = config["callback"]["port"]
    bch_rpcuser = config["bch"]["rpcuser"]
    bch_rpcpass = config["bch"]["rpcpassword"]
    bch_rpcport = config["bch"]["rpcport"]
    btc_rpcuser = config["btc"]["rpcuser"]
    btc_rpcpass = config["btc"]["rpcpassword"]
    btc_rpcport = config["btc"]["rpcport"]
    electrum_bin = config["btc"]["bin"]
    btc_wallet_path = config["btc"]["wallet_file"]
    bch_wallet_path = config["bch"]["wallet_file"]
    start_btc_daemon(electrum_bin,btc_wallet_path,btc_rpcuser,btc_rpcpass,btc_rpcport)
    start_bch_daemon(electron_bin,bch_wallet_path,bch_rpcuser,bch_rpcpass,bch_rpcport)
    for wish in wishlist["wishlist"]:
        if not wish["xmr_address"]:
            xmr_wallet = os.path.basename(config['monero']['wallet_file'])
            wish["xmr_address"] = get_unused_address(config,"xmr",wish["title"])
        if not wish["btc_address"]:
            wish["btc_address"] = get_unused_address(config,"btc")
        if not wish["bch_address"]:
            wish["bch_address"] = get_unused_address(config,"bch")


    #terminate all daemons

    #if they where launched stop them
    #"blindly try to stop any running bch/btc daemon"

    stop_bit_daemon(electrum_bin)
    stop_bit_daemon(electron_bin)


    monero_rpc_close_wallet(rpc_url)
    monero_daemon.terminate()
    monero_daemon.communicate()
    with open('your_wishlist.json', 'w') as f:
        json.dump(wishlist, f, indent=6) 
    create_new_wishlist()
    config["bch"]["bin"] = electron_bin
    config["btc"]["bin"] = electrum_bin
    config["wishlist"]["www_root"] == www_root
    with open('wishlist.ini', 'w') as configfile:
        config.write(configfile)

    con = sqlite3.connect('crypto_prices.db')
    cur = con.cursor()
    create_price_table = """ CREATE TABLE IF NOT EXISTS crypto_prices (
                                data default 0,
                                xmr integer,
                                btc integer,
                                bch integer
                            ); """
    cur.execute(create_price_table)
    sql = ''' INSERT INTO crypto_prices(data,xmr,btc,bch)
    VALUES (0,0,0,0)'''
    cur.execute(sql)
    con.commit()
    con.close()

    db_make_modified()

    print("Finished. Run 'start_daemons.py' to complete the install.")

    #clear memory cache (linux)
    os.system('sync')
    open('/proc/sys/vm/drop_caches','w').write("1\n")

def db_make_modified():
    #remove modified.db if exists
    con = sqlite3.connect('modified.db')
    cur = con.cursor()
    create_modified_table = """ CREATE TABLE IF NOT EXISTS modified (
                                data integer default 0,
                                comment integer default 1,
                                wishlist integer default 1
                            ); """
    cur.execute(create_modified_table)
    sql = ''' INSERT INTO modified(data,comment,wishlist)
    VALUES (?,?,?)'''
    cur.execute(sql, (0,2,2))
    con.commit()
    con.close()

def stop_bit_daemon(daemon_dir):
    if "electron" in daemon_dir:
        run_args = [daemon_dir, "daemon", "stop", "--testnet"]
    else:
        run_args = [daemon_dir, "stop", "--testnet"]
    stop_daemon = subprocess.Popen(run_args)
    stop_daemon.communicate()

def wish_prompt():
    wish={}
    wish["title"] = input('Wish Title:')
    wish["goal"] = float(input('USD Goal:'))
    wish["desc"] = input('Wish Description:')

    wish_add(wish)
    add = input('Add another wish y/n:')
    if 'y' in add.lower():
        wish_prompt()
    else:
        print("Wishlist created, lets add donation addresses to them..")
    


def wish_add(wish):
    if os.path.isfile("your_wishlist.json"):
        with open('your_wishlist.json') as f:
            wishlist = json.load(f)
    else:
        wishlist = {}
        wishlist["wishlist"] = []

    wish = {
    "goal_usd":wish["goal"],
    "hours": "",
    "title": wish["title"],
    "description":wish["desc"],
    "bch_address":"",
    "btc_address":"",
    "xmr_address":"",
    "type": "gift"
    }
    wish = wish.copy()
    wishlist["wishlist"].append(wish)
    with open('your_wishlist.json','w+') as f:
        json.dump(wishlist, f,indent=6)

if __name__ == "__main__":
    #os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"cwd: {os.getcwd()}")
    for proc in psutil.process_iter():
        # check whether the process name matches
        if "monero-wallet-" in proc.name():
            print(proc.name())
            proc.kill()
        if 'electrum' in proc.name().lower():
            proc.kill()
        if 'electron' in proc.name().lower():
            proc.kill()
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    main(config)

'''

n('The addresses in this wallet are not bitcoin addresses.
e.g. tb1qn..q6 (length: 42)')

'''