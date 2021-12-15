
import pprint
import json
from datetime import datetime
import cryptocompare
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
import _thread as thread
import psutil

#Api key of "-" appears to work currently, this may change,
cryptocompare.cryptocompare._set_api_key_parameter("-")

#need to get these from the monero wallet - these are just placeholders for now
viewkey = "716f1c5f49d46262095b8e52203e28148b0e36f9ca4571f6150db35d72752008"
main_address = "45BJBhJDxHZ25ubmcCNg1UYaZ8DpoeqXLRYaaZKuAVbAB6Nt63zNs6cGwkeBgRR1x5jHj9xaKvbzxVwwEeZqRoPuTxYGNNH"
percent_buffer = 0.05


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

def address_create_notify(create=1,notify=1,addr=""):
    global http_server
    global electrum_path
    if create == 1:
        stream = os.popen(f".{electrum_path} createnewaddress -w {wallet_path} --testnet")
        output = stream.read()
        #that was fun. address had a newline on it.
        address = output.replace("\n","")
        print(address)
    if notify == 1:
        if addr != "":
            address = addr
        thestring = f".{electrum_path} notify {address} {http_server} --testnet"
        print(thestring)
        stream = os.popen(thestring)
        output = stream.read()
        print(output)
    return(address)


def getPrice(crypto,offset):
    data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
    #print(f"[{crypto}]:{data[str(crypto)]['USD']}")
    value = float(data[str(crypto)]["USD"])
    #print(f"value = {value}")
    return(float(value) - (float(value) * float(offset)))

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
    global www_root
    if xmr_btc == "xmr":
        uri = "monero"
        logo = "logo3.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=7,
        border=4,
    )
    elif xmr_btc == "btc":
        uri = "bitcoin"
        logo = "BTC_Logo.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=7,
        border=4,
    )
    else:
        uri = "bitcoincash"
        
        logo = "bitcoin-cash-bch-logo.png"
        thumnail = (60, 60)
        qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=7,
        border=4,
    )
    try:
        if not os.path.isdir(os.path.join(www_root,'qrs')):
            os.mkdir(os.path.join(www_root,"qrs"))
        pass
    except Exception as e:
        raise e

    title = address[0:12]



    data = f"{uri}:{address}"
    qr.add_data(data)
    qr.make(fit=True)
    #img = qr.make_image(fill_color="black", back_color=(62,62,62))
    img = qr.make_image(fill_color=(62,62,62), back_color="white")
    img.save(os.path.join(www_root,"qrs",f"{title}.png"))
    f_logo = os.path.join("qrs",logo)
    logo = Image.open(f_logo)
    logo = logo.convert("RGBA")
    print(logo.size)
    im = Image.open(os.path.join(www_root,"qrs",f"{title}.png"))
    im = im.convert("RGBA")
    logo.thumbnail(thumnail)
    im.paste(logo,box=(142,142),mask=logo)
    #im.show()
    im.save(os.path.join(www_root,"qrs",f"{title}.png"))

def dump_json(wishlist):
    global www_root
    with open(os.path.join(www_root,"data",'wishlist-data.json'), 'w+') as f:
        json.dump(wishlist, f, indent=6) 

#get input from a used wallet
def load_old_txs():
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
                

def create_new_wishlist(config):
    global wishes, btc_info
    global viewkey, main_address
    global wallet_path, electrum_path
    global wishes
    global percent_buffer
    global btc_info
    #load wishlist from json file
    with open("your_wishlist.json", "r") as f:
        wishlist = json.load(f)

    for wish in wishlist["wishlist"]:
        pprint.pprint(wish)
        goal = wish["usd_goal"]
        desc = wish["description"]
        address = wish["xmr_address"]
        btc_address = wish["btc_address"]
        bch_address = wish["bch_address"]
        hours = wish["hours"]
        w_type = wish["type"]
        title = wish["title"]

        usd_hour_goal = goal
        if hours:
            goal += (float(usd_hour_goal) * float(percent_buffer)) 
            goal *= hours
        else:
            goal *= float(percent_buffer)

        app_this = { 
                    "goal_usd":goal, #these will be in usd
                    "usd_total":0, #usd - if you cash out for stability
                    "contributors":0,
                    "description": desc,
                    "percent": 0,
                    "hours": hours, # $/h
                    "type": w_type,
                    "created_date": str(datetime.now()),
                    "modified_date": str(datetime.now()),
                    "author_name": "",
                    "author_email": "",
                    "id": address[0:12],
                    "qr_img_url_xmr": f"qrs/{address[0:12]}.png",
                    "qr_img_url_btc": f"qrs/{btc_address[0:12]}.png",
                    "qr_img_url_bch": f"qrs/{bch_address[0:12]}.png",
                    "title": title,
                    "btc_address": btc_address,
                    "bch_address": bch_address,
                    "xmr_address": address,
                    "btc_total": 0,
                    "xmr_total": 0,
                    "hour_goal": usd_hour_goal,
                    "history": []
        } 
        wishes.append(app_this)
        put_qr_code(address,"xmr")
        put_qr_code(btc_address,"btc")
        put_qr_code(bch_address,"bch")
        info = {
        "address":btc_address,
        "confirmed":0,
        "unconfirmed":0,
        "contributors":0,
        "history":[]
        }
        btc_info.append(info)
        info = {
        "address":bch_address,
        "confirmed":0,
        "unconfirmed":0,
        "contributors":0,
        "history":[]
        }
        bch_info.append(info)

    
    thetime = datetime.now()
    total = {
        "total": 0,
        "contributors": 0,
        "modified": str(thetime),
        "title": "",
        "description": "",
        "image": "",
        "url": "",
        "viewkey": viewkey,
        "main_address": main_address,
        "protocol": "v3"
    }

    #search wallet for 'in' history, then compare addresses to our new list.
    #if matching address are found then contributors are +=1'd and amount+=amount.
    #monero-wallet-rpc daemon must be running ofcourse
    #load_old_txs()

    the_wishlist = {}
    the_wishlist["wishlist"] = wishes
    the_wishlist["metadata"] = total


    with open(os.path.join(www_root,"data","wishlist-data.json"), "w+") as f:
        json.dump(the_wishlist,f, indent=4)

    #create the addresses/metadata list
    btc_json = {}
    btc_metadata = {
    "date_modified": str(datetime.now())
    }
    btc_json["addresses"] = btc_info
    btc_json["metadata"] = btc_metadata

    with open(os.path.join(www_root,'data','wishlist-data-btc.json'), 'w+') as f:
        json.dump(btc_json, f, indent=6)  

    bch_json = {}
    bch_metadata = {
    "date_modified": str(datetime.now())
    }
    bch_json["addresses"] = bch_info
    bch_json["metadata"] = bch_metadata

    with open(os.path.join(www_root,'data','wishlist-data-bch.json'), 'w+') as f:
        json.dump(bch_json, f, indent=6)  

    '''
    btc_history = []
    with open('btc-history.json', 'w+') as f:
        json.dump(btc_history, f, indent=2)
    
    btc_conf_balance = {"balance":0}
    with open("btc-confirmed-balance.json", "w+") as f:
        json.dump(btc_conf_balance, f, indent=2)
    '''
    return 


def start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,wallet_file=None,remote_node=None):
    global wallet_dir
    rpc_args = [ 
        f".{rpc_bin_file}", 
        "--wallet-dir", wallet_dir,
        "--rpc-bind-port", rpc_port,
        "--disable-rpc-login", "--stagenet"
    ]
    monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)
    kill_daemon = 0
    print("Starting Monero rpc...")
    for line in iter(monero_daemon.stdout.readline,''):
        print(str(line.rstrip()))
        if b"Error" in line.rstrip() or b"Failed" in line.rstrip():
            kill_daemon = 1
            break
        if b"Starting wallet RPC server" in line.rstrip():
            print("Success!")
            break
        time.sleep(1)
    if kill_daemon == 1:
        monero_daemon.terminate()
        sys.exit(1)

    #Starting rpc server successful. lets wait until its fully online
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
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
        info = rpc_connection.open_wallet({"filename": wallet_fname})
        info = rpc_connection.set_daemon({"address": remote_node})

def monero_rpc_online(rpc_url):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.get_version()
        return True
    except Exception as e:
        print(e)
        return False

def monero_rpc_close_wallet(rpc_url):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.close_wallet()
        pass
    except Exception as e:
        print(e)
        sys.exit(1)

def create_monero_wallet(config):
    global wallet_dir
    rpc_port = config["monero"]["daemon_port"]
    if rpc_port == "":
        rpc_port = 18082
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
    remote_node = "http://" + config["monero"]["remote_node"]
    print(remote_node)
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
    #monero_wallet_rpc is set by a global,
    monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url)
        

    print("Creating a Monero wallet..")
    letters = string.ascii_lowercase
    try:
        #print(rpc_url)
        rpc_connection = AuthServiceProxy(service_url=rpc_url)
        #label could be added
        wallet_fname = "monero_" + ''.join(random.choice(letters) for i in range(10))
        params={
                "filename": wallet_fname,
                "language": "English"
                }
        info = rpc_connection.create_wallet(params)
        info = rpc_connection.open_wallet({"filename": wallet_fname})
        info = rpc_connection.get_height()
        #to get block height data we need to use /json_rpc
        rpc_remote = remote_node + "/json_rpc"
        remote_rpc_connection = AuthServiceProxy(service_url=rpc_remote)
        data = remote_rpc_connection.get_info()
        view_key = rpc_connection.query_key({"key_type": "view_key"})["key"]
        mnemonic = rpc_connection.query_key({"key_type": "mnemonic"})["key"]
        spend_key = rpc_connection.query_key({"key_type": "spend_key"})["key"]
        main_address = rpc_connection.get_address()["address"]
        print("*************[Monero Wallet]*************")
        print(f"Your Monero wallet seed is:") 
        print(mnemonic)
        print(f"restore height: {data['height']}")
        print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
        print("*************[Monero Wallet]*************")
        print(f"setting block height from remote node to: {data['height']}")

        info = rpc_connection.set_daemon({"address": remote_node})

        #time.sleep(10)
        info = rpc_connection.get_height()
        print(info)
        info = rpc_connection.refresh({"start_height": (data['height'] - 1)})
        print("Saving monero wallet")
        rpc_connection.store() 

        #Close in a thread as this blocks for a few seconds TODO
        rpc_connection.close_wallet()
        wallet_path = os.path.join(wallet_dir,wallet_fname)
        config["monero"]["wallet_file"] = wallet_path

        with open('wishlist.ini', 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        print(e)
        time.sleep(3)
        print("Connecting to daemon...")
    return monero_daemon

def create_bch_wallet(config):
    global wallet_dir
    electron_bin = config["bch"]["bin"]
    #todo - strange 
    for x in os.listdir("bin"):
        if "Electron-Cash" in x:
            electron_bin = os.path.join("bin",x,"electron-cash")
    if electron_bin == "":
        return False
    letters = string.ascii_lowercase
    wallet_fname = "cash_" + ''.join(random.choice(letters) for i in range(10)) 
    wallet_path = os.path.join(wallet_dir,wallet_fname)
    #print(wallet_path)
    run_args = [
        electron_bin, "create", "-w", wallet_path, "--testnet"
        ]
    bch_bin = subprocess.Popen(run_args,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        bch_bin.communicate(input=b"\n")
        with open(wallet_path, "r") as f:
            bch_data = json.load(f)
        print("*************[Bitcoin-Cash wallet]*************")
        print("Your Bitcoin-Cash wallet seed is:")
        print(f"{bch_data['keystore']['seed']}")
        print(f"format:{bch_data['keystore']['seed_type']} derivation: {bch_data['keystore']['derivation']}")
        print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
        print("*************[Bitcoin-Cash wallet]*************")
        config["bch"]["wallet_file"] = wallet_path
        with open('wishlist.ini', 'w') as configfile:
            config.write(configfile)
        return config
        pass
    except Exception as e:
        raise e

def create_btc_wallet(config):
    global wallet_dir
    electron_bin = config["btc"]["bin"]
    #python3 run_electrum create -w lol --offline
    for x in os.listdir("bin"):
        if "Electrum-" in x:
            electrum_bin = os.path.join("bin",x,"run_electrum")
    if electron_bin == "":
        return False
    letters = string.ascii_lowercase
    wallet_fname = "bitcoin_" + ''.join(random.choice(letters) for i in range(10)) 
    wallet_path = os.path.join(wallet_dir,wallet_fname)
    #print(wallet_path)
    run_args = [
        electrum_bin, "create", "-w", wallet_path, "--offline", "--testnet"
        ]
    bch_bin = subprocess.Popen(run_args,stdout=subprocess.PIPE)
    #wait until finished
    bch_bin.communicate()

    with open(wallet_path, "r") as f:
        bch_data = json.load(f)
    print("*************[Bitcoin wallet]*************")
    print("Your Bitcoin-Cash wallet seed is:")
    print(f"{bch_data['keystore']['seed']}")
    print(f"format:{bch_data['keystore']['seed_type']} derivation: {bch_data['keystore']['derivation']}")
    print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
    print("*************[Bitcoin wallet]*************")
    config["btc"]["wallet_file"] = wallet_path
    with open('wishlist.ini', 'w') as configfile:
        config.write(configfile)
    return config

def main(config):
    global www_root
    www_root = config["wishlist"]["www_root"]
    #Error checks needed here on user inputs
    if not www_root:
        www_root = input('Where is your root website folder (e.g. /var/www/html):')
    www_data_dir = os.path.join(www_root,"data")
    www_qr_dir = os.path.join(www_root,"qrs")
    if not os.path.isdir(os.path.join(www_data_dir)):
        os.mkdir(www_data_dir)
    if not os.path.isdir(os.path.join(www_qr_dir)):
        os.mkdir(www_qr_dir)
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
            rpc_port = config["monero"]["daemon_port"]
            if rpc_port == "":
                rpc_port = 18082
            rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
            remote_node = "http://" + config["monero"]["remote_node"]

            monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_file,remote_node)
            if monero_rpc_online(rpc_url) == False:
                print("Error: monero rpc not online")
                sys.exit(1)

    if not config["bch"]["wallet_file"]:
        config = create_bch_wallet(config)
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
        config = create_btc_wallet(config)
    else:
        if not os.path.isfile(config["btc"]["wallet_file"]):
            print("***********************************")
            print("BTC wallet missing! see wishlist.ini")
            print("***********************************")
            sys.exit(1)
    print('Start the BTC daemon / open wallet')
    electrum_bin = config["btc"]["bin"]

    btc_wallet_path = config["btc"]["wallet_file"]
    run_args = [
    electrum_bin, "daemon", "-d", "--testnet"
    ]
    btc_daemon = subprocess.Popen(run_args, stdout=subprocess.PIPE)
    btc_daemon.communicate()
    stream = os.popen(f"{electrum_bin} load_wallet -w {btc_wallet_path} --testnet")
    stream.read()

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

    for wish in wishlist["wishlist"]:
        if not wish["xmr_address"]:
            rpc_connection = AuthServiceProxy(service_url=rpc_url)
            xmr_wallet = os.path.basename(config['monero']['wallet_file'])
            rpc_connection.open_wallet({"filename": xmr_wallet })
            #label could be added
            params={
                    "account_index":0,
                    "label": wish["title"]
                    }
            info = rpc_connection.create_address(params)
            wish["xmr_address"] = info["address"]
    
        if not wish["btc_address"]:
            btc_wallet_path = config['btc']['wallet_file']
            stream = os.popen(f"{electrum_bin} createnewaddress -w {btc_wallet_path} --testnet")
            output = stream.read()
            btc_address = output.replace("\n","")
            wish["btc_address"] = btc_address

        if not wish["bch_address"]:
            bch_wallet_path = config["bch"]["wallet_file"]
            stream = os.popen(f"{electron_bin} createnewaddress -w {bch_wallet_path} --testnet")
            output = stream.read()
            btc_address = output.replace("\n","")
            wish["bch_address"] = btc_address
    pprint.pprint(wishlist)

    #terminate all daemons

    #if they where launched stop them
    #"blindly try to stop any running bch/btc daemon"

    print(f"electron:{electron_bin}")
    print(f"electrum:{electrum_bin}")
    run_args = [
    electron_bin, "daemon", "stop", "--testnet"
    ]
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()
    run_args = [
    electrum_bin, "stop", "--testnet"
    ]
    btc_daemon = subprocess.Popen(run_args)
    btc_daemon.communicate()

    if monero_online == 1:
        monero_daemon.terminate()
        monero_daemon.communicate()
    with open('your_wishlist.json', 'w') as f:
        json.dump(wishlist, f, indent=6) 
    create_new_wishlist(config)
    config["bch"]["bin"] = electron_bin
    config["btc"]["bin"] = electrum_bin
    config["wishlist"]["www_root"] == www_root
    with open('wishlist.ini', 'w') as configfile:
        config.write(configfile)
    #bch daemon 

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
    "usd_goal":wish["goal"],
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
    for proc in psutil.process_iter():
        # check whether the process name matches
        if "monero-wallet-" in proc.name():
            print(proc.name())
            proc.kill()
        if 'electrum' in proc.name():
            proc.kill()
        if 'electron' in proc.name():
            proc.kill()
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    main(config)

