
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
from start_daemons import start_btc_daemon
import textwrap
from colorama import Fore, Back, Style
import shutil
#bitcoin - have to ./make_libsecp256k1.sh 

viewkey = ""
main_address = ""

#Api key of "-" appears to work currently, this may change,

#need to get these from the monero wallet - these are just placeholders for now
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

def address_create_notify(bin_dir,wallet_path,port,addr="",create=1,notify=1):
    print("address_create_notify")
    print(f'bin dir = {bin_dir}')
    print(f'walletpath = {wallet_path}')
    print(f'port:{port}')
    if create == 1:
        thestring = f"./{bin_dir} createnewaddress -w {wallet_path} --testnet"
        print(f'cmd : {thestring}')
        stream = os.popen(thestring)
        output = stream.read()
        #that was fun. address had a newline on it.
        address = output.replace("\n","")
    if notify == 1:
        if addr != "":
            address = addr
        thestring = f"./{bin_dir} notify {address} {port} --testnet"
        print(thestring)
        stream = os.popen(thestring)
        output = stream.read()
        print(output)
    return(address)

def get_xmr_subaddress(rpc_url,wallet_file,title):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    xmr_wallet = os.path.basename(wallet_file)
    print(f"xmr wallet file: {xmr_wallet}")
    #i dont think we need to open one
    #rpc_connection.open_wallet({"filename": wallet_file, "password": "" })
    #label could be added
    params={
            "account_index":0,
            "label": title
            }
    info = rpc_connection.create_address(params)
    return info["address"]

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
        logo = "monero-xmr-logo.png"
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
        uri = "bchtest"
        
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
    if os.path.isfile(os.path.join(www_root,"qrs",f"{title}.png")):
        #dont bother recreating the qr image
        #could cause issues if you want to do that though
        return


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
                    "bch_address": ("bchtest:" + bch_address),
                    "xmr_address": address,
                    "btc_total": 0,
                    "xmr_total": 0,
                    "bch_total": 0,
                    "hour_goal": usd_hour_goal,
                    "xmr_history": [],
                    "bch_history": [],
                    "btc_history": [],
                    "btc_confirmed": 0,
                    "btc_unconfirmed": 0,
                    "bch_confirmed": 0,
                    "bch_unconfirmed": 0
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
        "status": "OK"
        "protocol": "v3"
    }

    #search wallet for 'in' history, then compare addresses to our new list.
    #if matching address are found then contributors are +=1'd and amount+=amount.
    #monero-wallet-rpc daemon must be running ofcourse
    #load_old_txs()

    the_wishlist = {}
    the_wishlist["wishlist"] = wishes
    the_wishlist["metadata"] = total
    the_wishlist["archive"] = []

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
        print("wallet file was none!")
        rpc_args = [ 
            f".{rpc_bin_file}", 
            "--wallet-file", wallet_file,
            "--rpc-bind-port", rpc_port,
            "--disable-rpc-login", "--stagenet",
            "--daemon-address", remote_node,
            "--password", ""
        ]

    print("at monero_daemona")
    pprint.pprint(rpc_args)
    monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)

    print("problem")
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
                rpc_remote = remote_node + "/json_rpc"
                remote_rpc_connection = AuthServiceProxy(service_url=rpc_remote)
                data = remote_rpc_connection.get_info()
                info = rpc_connection.refresh({"start_height": (data['height'] - 1)})
                rpc_connection.store()
            break
        time.sleep(1)
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
    dummy_wallet = os.path.join(wallet_dir,"dummy_wallet")
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
    monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,None,remote_node)
        

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
        info = rpc_connection.open_wallet({"filename": wallet_fname,"password": ""})
        info = rpc_connection.get_height()
        #to get block height data we need to use /json_rpc
        rpc_remote = remote_node + "/json_rpc"
        remote_rpc_connection = AuthServiceProxy(service_url=rpc_remote)
        data = remote_rpc_connection.get_info()
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
        wallet_path = os.path.join(wallet_dir,wallet_fname)
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

        #restore from viewkey
        
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
        #pprint.pprint(rpc_args)
        test_string = ""
        for x in rpc_args:
            test_string += x + " "
        print(test_string)
        monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)
        print("Busy creating a view-only Monero wallet...")
        while not os.path.isfile(wallet_path):
            time.sleep(1)
        print("View-only wallet created.")
        #remove the broken wallet file(??) (in testing i had to remove the wallet file for some reason)
        monero_daemon.terminate()
        monero_daemon.communicate()
        os.remove(wallet_path)
        #close it so we can set wallet dir(??)
        
        #start with the keys file only
        #special
        print("Loading view-only wallet...")
        monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_path,remote_node)
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
        print(f"*************[{Style.BRIGHT}{Fore.GREEN}Bitcoin-Cash {Style.RESET_ALL}wallet]*************")
        print("Your Bitcoin-Cash wallet seed is:")
        print(f"{bch_data['keystore']['seed']}")
        print(f"format:{bch_data['keystore']['seed_type']} derivation: {bch_data['keystore']['derivation']}")
        print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
        print("*************[Bitcoin-Cash wallet]*************")
        input("Write your seed down on paper or you can never spend money you receive \n Press enter to continue >>")
        config["bch"]["wallet_file"] = wallet_path
        with open('wishlist.ini', 'w') as configfile:
            config.write(configfile)
        #stop bch daemon
        stop_bit_daemon(electron_bin)
        secure_delete(wallet_path,passes=3)
        run_args = [
        electron_bin, "restore", "-w", wallet_path, "--testnet", bch_data['keystore']['xpub']
        ]
        bch_bin = subprocess.Popen(run_args,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        bch_bin.communicate()
        #
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
        electron_bin, "create", "-w", wallet_path, "--offline", "--testnet"
        ]
    bch_bin = subprocess.Popen(run_args,stdout=subprocess.PIPE)
    #wait until finished
    bch_bin.communicate()   

    with open(wallet_path, "r") as f:
        bch_data = json.load(f)
    print(f"*************[{Style.BRIGHT}{Fore.RED}Bitcoin {Style.RESET_ALL}wallet]*************")
    print("Your Bitcoin-Cash wallet seed is:")
    print(f"{bch_data['keystore']['seed']}")
    print(f"format:{bch_data['keystore']['seed_type']} derivation: {bch_data['keystore']['derivation']}")
    print("Please keep your seed information in a safe place; if you lose it, you will not be able to restore your wallet")
    print("*************[Bitcoin wallet]*************")
    input("Write your seed down on paper or you can never spend money you receive \n Press enter to continue >>")

    config["btc"]["wallet_file"] = wallet_path
    with open('wishlist.ini', 'w') as configfile:
        config.write(configfile)
    #stop_bit_daemon(electrum_bin)

    secure_delete(wallet_path,passes=3)
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
            remote_node = "http://" + config["monero"]["remote_node"]
            monero_daemon = start_monero_rpc(monero_wallet_rpc,rpc_port,rpc_url,wallet_file,remote_node)

    if not config["bch"]["wallet_file"]:
        #maybe we dont have to close the daemon in create wallet
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
    print(f"time to break: {btc_wallet_path} {electrum_bin}")
    start_btc_daemon(electrum_bin,btc_wallet_path)
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
    for wish in wishlist["wishlist"]:
        if not wish["xmr_address"]:
            xmr_wallet = os.path.basename(config['monero']['wallet_file'])
            wish["xmr_address"] = get_xmr_subaddress(rpc_url,xmr_wallet,wish["title"])
        if not wish["btc_address"]:
            wish["btc_address"] = address_create_notify(electrum_bin,btc_wallet_path,port,addr="",create=1,notify=0)
        if not wish["bch_address"]:
            wish["bch_address"] = address_create_notify(electron_bin,bch_wallet_path,port,addr="",create=1,notify=0)


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


    #move the html files
    try:
        #(qrs dir already made)
        js_dir = os.path.join(www_root,"js")
        logos_dir = os.path.join(www_root,"logos")
        images_dir = os.path.join(www_root,"images")
        if not os.path.isdir(js_dir):
            os.mkdir(js_dir)
        if not os.path.isdir(logos_dir):
            os.mkdir(logos_dir)
        if not os.path.isdir(images_dir):
            os.mkdir(images_dir)
        #copy the js file
        shutil.copy(os.path.join(".","html","js","app.js"),js_dir)
        shutil.copy(os.path.join(".","html","simple.css"),www_root)
        shutil.copy(os.path.join(".","html","lightbox.css  "),www_root)
        shutil.copy(os.path.join(".","qrs","bitcoin-cash-bch-logo.png"),logos_dir)
        shutil.copy(os.path.join(".","qrs","BTC_Logo.png"),logos_dir)
        shutil.copy(os.path.join(".","qrs","monero-xmr-logo.png"),logos_dir)
        shutil.copy(os.path.join(".","html","images","close.png"),images_dir)
        shutil.copy(os.path.join(".","html","images","loading.gif"),images_dir)
        shutil.copy(os.path.join(".","html","images","next.png"),images_dir)
        shutil.copy(os.path.join(".","html","images","plowsof.png"),images_dir)
        shutil.copy(os.path.join(".","html","images","prev.png"),images_dir)
        shutil.copy(os.path.join(".","html","js","lightbox-plus-jquery.min.js"),js_dir)

    except Exception as e:
        raise e

    print("Finished. Run 'start_daemons.py' to complete the install.")

    #clear memory cache (linux)
    os.system('sync')
    open('/proc/sys/vm/drop_caches','w').write("1\n")

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