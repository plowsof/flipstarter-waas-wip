import os
import json
import requests
import configparser
import subprocess
import time
import sys
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException
import threading 
from filelock import FileLock
import pprint
import cryptocompare
import sqlite3 
import psutil
cryptocompare.cryptocompare._set_api_key_parameter("")


wallet_dir = os.path.join(os.path.abspath(os.path.join(os.getcwd(),"wallets")))
www_root = ""
def monero_rpc_online(rpc_url):
    print("hello?")
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        info = rpc_connection.get_version()
        print("return true")
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
        #if rpc is online but no wallet open this errors, but ok to ignore
        print(e)

def monero_rpc_open_wallet(rpc_url,wallet_file):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        wallet_fname = os.path.basename(wallet_file)
        info = rpc_connection.open_wallet({"filename": wallet_fname})
        pass
    except Exception as e:
        print(e)
        sys.exit(1)

def find_working_node(node_list):
    max_retries = 30
    num_retries = 0
    node_online = 0
    for remote_node in node_list:
        try:
            rpc_url = "http://" + str(remote_node) + "/json_rpc"
            #this will retry the url for 30 seconds (built in to monerorpc library)
            rpc_connection = AuthServiceProxy(service_url=rpc_url)
            print(f"trying {rpc_url}")
            info = rpc_connection.get_info()
            if info["status"] != "OK":
                continue
            else:
                node_online = 1
                break
        except Exception as e:
            continue

    if node_online == 0:
        print("Number of retries exceeded with all backup nodes. monero node not started")
        return False
    else:
        return remote_node

def start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file=None):
    global wallet_dir
    print(f"{wallet_file}")
    print(f"{rpc_port}")
    print(f"walletfile = {wallet_file}")
    print(f"we are using remote node {remote_node}")

    rpc_args = [ 
        f"{rpc_bin_file}", 
        "--wallet-file", wallet_file,
        "--rpc-bind-port", rpc_port,
        "--disable-rpc-login",
        "--tx-notify", f"/usr/bin/python3 {os.path.join(os.path.abspath(os.path.join(os.getcwd(),'notify_xmr_vps_pi.py')))} %s",
        "--daemon-address", remote_node,
        "--stagenet", "--password", ""
    ]
    for x in rpc_args:
        print(x)
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
        #time.sleep(1)
    if kill_daemon == 1:
        print(line.rstrip())
        monero_daemon.terminate()


    #Starting rpc server successful. lets wait until its fully online
    print(rpc_url)
    print(wallet_file)
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    num_retries = 0
    while True:
        try:
            print("Hello world")
            info = rpc_connection.get_version()
            print("Monero RPC server online.")
            print(info)
            return monero_daemon
        except Exception as e:
            print(e)
            print("Trying again..")
            if num_retries > 30:
                #the lights are on but nobodys home, exit
                print("Unable to communiucate with monero rpc server. Exiting")
                sys.exit(1)
            time.sleep(1)
            num_retries += 1

def set_up_notify(bin_path,wallet_path,address,http_server,symbol):
    if ":" in address:
        address = address.split(':')[1]
    if symbol == "btc":
        thestring = f"{bin_path} notify {address} {http_server} --testnet"
    else:
        thestring = f"{bin_path} notify {address} {http_server} --testnet"
    print(thestring)
    stream = os.popen(thestring)
    output = stream.read()
    #print(output)
    return(address)

def getJson():
    global www_root
    wishlist_file  = os.path.join(www_root,"data","wishlist-data.json")
    print(f"{wishlist_file}")
    with open(wishlist_file, "r") as f:
        return json.load(f)

def start_bch_daemon(electron_bin,wallet_file,rpcuser,rpcpass,rpcport):
    run_args = [
    electron_bin, "daemon", "stop", "--testnet"
    ]
    
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()
    #set rpc port/creds
    rpc_user = [
    electron_bin, "setconfig", "rpcuser", rpcuser, "--testnet"
    ]
    bch_daemon = subprocess.Popen(rpc_user)
    bch_daemon.communicate()
    rpc_pass = [
    electron_bin, "setconfig", "rpcpassword", rpcpass, "--testnet"
    ]
    bch_daemon = subprocess.Popen(rpc_pass)
    bch_daemon.communicate()
    rpc_port = [
    electron_bin, "setconfig", "rpcport", rpcport, "--testnet"
    ]
    bch_daemon = subprocess.Popen(rpc_port)
    bch_daemon.communicate()
    '''
    curl --data-binary '{"id":"curltext","method":"daemon","params":{"config_options":{"subcommand":"load_wallet", "wallet_path":"/home/user/.electrum/testnet/wallets/test_std_asdasd", "password":"1234"}}}' http://user:pass@127.0.0.1:7778
    curl --data-binary '{"id":"curltext","method":"getseed"}' http://user:pass@127.0.0.1:7778
    '''
    run_args = [
    electron_bin, "daemon", "start", "--testnet"
    ]
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()
    run_args = [
    electron_bin, "daemon", "load_wallet", "-w", wallet_file, "--testnet"
    ]
    print(run_args)
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()

def start_btc_daemon(electrum_bin,wallet_file,rpcuser,rpcpass,rpcport):
    run_args = [
    electrum_bin, "stop", "--testnet"
    ]
    btc_daemon = subprocess.Popen(run_args)
    btc_daemon.communicate()

    #set rpc port/creds
    rpc_user = [
    electrum_bin, "setconfig", "rpcuser", rpcuser, "--testnet", "--offline"
    ]
    btc_daemon = subprocess.Popen(rpc_user)
    btc_daemon.communicate()
    rpc_pass = [
    electrum_bin, "setconfig", "rpcpassword", rpcpass, "--testnet", "--offline"
    ]
    btc_daemon = subprocess.Popen(rpc_pass)
    btc_daemon.communicate()
    rpc_port = [
    electrum_bin, "setconfig", "rpcport", rpcport, "--testnet", "--offline"
    ]
    btc_daemon = subprocess.Popen(rpc_port)
    btc_daemon.communicate()

    run_args = [
    electrum_bin, "daemon", "-d", "--testnet"
    ]
    print(run_args)
    btc_daemon = subprocess.Popen(run_args)
    btc_daemon.communicate()
    run_args = [
    electrum_bin, "load_wallet", "-w", wallet_file, "--testnet"
    ]
    print(run_args)
    btc_daemon = subprocess.Popen(run_args)
    btc_daemon.communicate()

    #btc_open_wallet(wallet_file,rpcuser,rpcpass,rpcport)

#this does not work
#the wallet_path params must be wrong
def btc_rpc_createnewaddress(wallet,rpcuser,rpcpass,rpcport):
    print(f"try open {wallet}")
    url = f"http://{rpcuser}:{rpcpass}@localhost:{rpcport}"
    payload = {
        "method": "createnewaddress",
        "params": [{
        "wallet_path": wallet
        }
        ],
        "jsonrpc": "2.0",
        "id": 0,
    }
    returnme = requests.post(url, json=payload).json()
    pprint.pprint(returnme)

def main(config):
    global www_root
    rpc_bin_file = config["monero"]["bin"]
    rpc_port = config["monero"]["daemon_port"]
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
    wallet_file = config["monero"]["wallet_file"]
    fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
    list_remote_nodes = []
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

    www_root = config["wishlist"]["www_root"]

    if monero_rpc_online(rpc_url) == True:
        monero_rpc_close_wallet(rpc_url)
        #monero_rpc_open_wallet(rpc_url,wallet_file)
    remote_node = find_working_node(list_remote_nodes)

    if remote_node:
        start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file)

    electrum_path = config["btc"]["bin"]
    btc_wallet_path = config["btc"]["wallet_file"]
    rpcuser = config["btc"]["rpcuser"]
    rpcpass = config["btc"]["rpcpassword"]
    rpcport = config["btc"]["rpcport"]
    start_btc_daemon(electrum_path,btc_wallet_path,rpcuser,rpcpass,rpcport)
    electron_path = config["bch"]["bin"]
    bch_wallet_path = config["bch"]["wallet_file"]
    rpcuser = config["bch"]["rpcuser"]
    rpcpass = config["bch"]["rpcpassword"]
    rpcport = config["bch"]["rpcport"]
    start_bch_daemon(electron_path,bch_wallet_path,rpcuser,rpcpass,rpcport)
    print("after bch daemon")

    http_port = config["callback"]["port"]
    http_server = "http://localhost:" + str(http_port)

    wish_list = getJson()

    for wish in wish_list["wishlist"]:
        if wish["btc_address"]:
            address = wish["btc_address"]
            set_up_notify(electrum_path,btc_wallet_path,address,http_server,"btc")

        if wish["bch_address"]:
            address = wish["bch_address"]
            print(address)
            set_up_notify(electron_path,bch_wallet_path,address,http_server,"bch")

    th = threading.Thread(target=refresh_html_loop, args=(remote_node,rpc_url,config,))
    th.start()
    th = threading.Thread(target=delete_clicks_db)
    th.start()
    th = threading.Thread(target=save_prices)
    th.start()
    #start the bitcoin listener
    os.system(f'/usr/bin/python3 notify_bch_btc.py {http_port}')


def getPrice(crypto):
    data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
    return(data[str(crypto)]["USD"])

def save_prices():
    while True:
        p_xmr = float(getPrice("XMR"))    
        p_btc = float(getPrice("BTC"))
        p_bch = float(getPrice("BCH"))

        con = sqlite3.connect('crypto_prices.db')
        cur = con.cursor()
        create_price_table = """ CREATE TABLE IF NOT EXISTS crypto_prices (
                                    data default 0,
                                    xmr integer,
                                    btc integer,
                                    bch integer
                                ); """
        cur.execute(create_price_table)
        
        sql = ''' UPDATE crypto_prices
                  SET xmr = ?,
                      bch = ?,
                      btc = ?
                  WHERE data = 0'''   
        cur.execute(sql, (p_xmr,p_bch,p_btc))
        con.commit()
        con.close()
        time.sleep(60*5)

def delete_clicks_db():
    while True:
        #20 clicks/day per ip.
        if os.path.isfile("clicks.db"):
            os.remove("clicks.db")
        time.sleep(60*60*24)

def refresh_html_loop(remote_node,local_node,config):
    global www_root
    print(f"remotenode: {remote_node}\n localnode : {local_node}")
    #static html refresh every 5 minutes
    rpc_url = "http://" + str(remote_node) + "/json_rpc"
    counter = 1
    while True: 
        #os.system(f'/usr/bin/python3 static_html_loop.py')
        
        www_root = config["wishlist"]["www_root"]
        wishlist = getJson()
        node_status = wishlist["metadata"]["status"]
        not_ok = 0
        list_modified = 0

        #save monero wallet file every 10 mins
        rpc_connection = AuthServiceProxy(service_url=rpc_url)
        rpc_local = AuthServiceProxy(service_url=local_node)


        try:
            rpc_local.store()
        except Exception as e:
            print(e)
            not_ok = 1
            for proc in psutil.process_iter():
                # check whether the process name matches
                if "monero-wallet-rpc" in proc.name():
                    proc.kill()
            rpc_bin_file = config["monero"]["bin"]
            rpc_port = config["monero"]["daemon_port"]
            rpc_url_local = "http://localhost:" + str(rpc_port) + "/json_rpc"
            wallet_file = config["monero"]["wallet_file"]
            list_remote_nodes = []
            fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
            for i in range(int(fallback_remote_nodes)):
                num = (i+1)
                list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

            remote_node = find_working_node(list_remote_nodes)
            if remote_node:
                start_monero_rpc(rpc_bin_file,rpc_port,rpc_url_local,remote_node,wallet_file)
                wishlist["metadata"]["status"] = "OK"
            not_ok = 0
        try:
            #sometimes the remote node is offline
            info = rpc_connection.get_info()
            #sometimes theres an issue with local rpc
            #need to separate
            if info["status"] != "OK":
                wishlist["metadata"]["status"] = "remote"
                not_ok = 1
            else:
                not_ok = 0
        except Exception as e:
            print(e)
            print("error - remote")
            wishlist["metadata"]["status"] = "remote"
            not_ok = 1
            list_remote_nodes = []
            fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
            for i in range(int(fallback_remote_nodes)):
                num = (i+1)
                list_remote_nodes.append(config["monero"][f"remote_node_{num}"])

            remote_node = find_working_node(list_remote_nodes)
            if remote_node:
                start_monero_rpc(rpc_bin_file,rpc_port,rpc_url_local,remote_node,wallet_file)
                wishlist["metadata"]["status"] = "OK"


        if not_ok == 1:
            if node_status != "remote":
               list_modified = 1
        else:
            if node_status != "OK":
                wishlist["metadata"]["status"] = "OK"
                list_modified = 1
        if list_modified == 1:
            wishlist_file  = os.path.join(www_root,"data","wishlist-data.json")
            lock = wishlist_file + ".lock"
            with FileLock(lock):
                #print("Lock acquired.")
                with open(wishlist_file, 'w+') as f:
                    json.dump(wishlist, f, indent=6)
        
        del rpc_connection
        del rpc_local
        time.sleep(60*10)

if __name__ == '__main__':
    config = configparser.ConfigParser()

    config.read('wishlist.ini')
    main(config)


'''
Start the monero daemon with the correct tx-notify file / wallet (from config)
Start the BCH / BTC daemons and set up notifys on each address.
Start listen.py
'''

