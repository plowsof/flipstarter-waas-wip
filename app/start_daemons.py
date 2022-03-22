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
from colorama import Fore, Back, Style
cryptocompare.cryptocompare._set_api_key_parameter("")
from helper_create import print_msg, print_err, bit_online, monero_rpc_online
import uuid
import notify_xmr_vps_pi
import asyncio
import random 

wallet_dir = os.path.join(os.path.abspath(os.path.join(os.getcwd(),"wallets")))
www_root = ""

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
    #if we're in stagenet mode, then throw error if node is mainnet
    max_retries = 30
    num_retries = 0
    node_online = 0
    print_msg("Finding a Monero remote node.")
    random.shuffle(node_list)
    for remote_node in node_list:
        try:
            rpc_url = "http://" + str(remote_node) + "/json_rpc"
            #this will retry the url for 30 seconds (built in to monerorpc library)
            rpc_connection = AuthServiceProxy(service_url=rpc_url)
            info = rpc_connection.get_info()
            print(info["nettype"])
            if os.environ["waas_mainnet"] == "1":
                if info["nettype"] != "mainnet":
                    print_err("You are connecting to a stagenet node. Please add a monero mainnet node to docker-compose.yml [restart required].")
                    sys.exit(1)
            else:
                if info["nettype"] != "stagenet":
                    print_err("You are connecting to a mainnet node. Please add a Monero stagenet node to docker-compose.yml [restart required].")
                    sys.exit(1)
            if info["status"] != "OK":
                print_msg("Retrying another node")
                continue
            else:
                node_online = 1
                break
        except Exception as e:
            print(e)
            continue

    if node_online == 0:
        print_err("Unable to connect to a Monero remote node.")
        return False
    else:
        print("found our node")
        return remote_node

def start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file=None,wow_xmr="monero"):
    global wallet_dir
    rpc_args = [ 
        f"{rpc_bin_file}", 
        "--wallet-file", wallet_file,
        "--rpc-bind-port", rpc_port,
        "--disable-rpc-login",
        "--daemon-address", remote_node,
        "--password", "", 
        "--tx-notify", f"/usr/local/bin/python3 /home/app/notify_xmr_vps_pi.py %s"
    ]
    if wow_xmr != "monero":
        rpc_args.append("wow")
     
    for x in rpc_args:
        print(x)
    if os.environ["waas_mainnet"] == "0":
        print("stagenet mode")
        rpc_args.append("--stagenet")
    monero_daemon = subprocess.Popen(rpc_args,stdout=subprocess.PIPE)
    kill_daemon = 0
    print("Starting Monero rpc...")
    for line in iter(monero_daemon.stdout.readline,''):
        print(str(line.rstrip()))
        if b"Error" in line.rstrip() or b"Failed" in line.rstrip() or b'specify --wallet-file' in line.rstrip() or b"failed" in line.rstrip():
            kill_daemon = 1
            break
        if b"Starting wallet RPC server" in line.rstrip():
            print("Success!")
            break
        #time.sleep(1)
    if kill_daemon == 1:
        monero_daemon.terminate()
        print_err(line.rstrip())
        sys.exit(1)


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
    
def getJson():
    global www_root
    wishlist_file  = os.path.join(www_root,"data","wishlist-data.json")
    print(f"{wishlist_file}")
    with open(wishlist_file, "r") as f:
        return json.load(f)

def start_bit_daemon(bin_file,wallet_file,rpcuser,rpcpass,rpcport):
    rpc_user = [bin_file, "setconfig", "rpcuser", rpcuser]
    rpc_pass = [bin_file, "setconfig", "rpcpassword", rpcpass]
    rpc_port = [bin_file, "setconfig", "rpcport", rpcport]
    if "electrum" in bin_file:
        stop_daemon = [bin_file, "stop"]
        load_wallet = [bin_file, "load_wallet", "-w", wallet_file]
        start_daemon = [bin_file, "daemon", "-d"]
        rpc_user.append("--offline")
        rpc_pass.append("--offline")
        rpc_port.append("--offline")
    else:
        stop_daemon = [bin_file, "daemon", "stop"]
        load_wallet = [bin_file, "daemon", "load_wallet", "-w", wallet_file]
        start_daemon = [bin_file, "daemon", "start"]
    if os.environ["waas_mainnet"] == "0":
        stop_daemon.append("--testnet")
        rpc_user.append("--testnet")
        rpc_pass.append("--testnet")
        rpc_port.append("--testnet")
        start_daemon.append("--testnet")
        load_wallet.append("--testnet")
    run_cmd(stop_daemon)
    run_cmd(rpc_user)
    run_cmd(rpc_pass)
    run_cmd(rpc_port)
    run_cmd(start_daemon)
    run_cmd(load_wallet)

def run_cmd(list_args):
    bch_daemon = subprocess.Popen(list_args)
    bch_daemon.communicate()

def main(config):
    local_ip = "localhost"
    global www_root
    rpc_bin_file = config["monero"]["bin"]
    rpc_port = config["monero"]["daemon_port"]
    rpc_url = "http://" + str(local_ip) + ":" + str(rpc_port) + "/json_rpc"
    wallet_file = config["monero"]["wallet_file"]
    if os.environ["waas_mainnet"] == "1":
        if "test" in wallet_file:
            print_err("You're using a Monero stagenet wallet in mainnet mode.\nConnect to this container and run make_wishlist.py to create a mainnet wallet")
            sys.exit(1)
    else:
        if "test" not in wallet_file:
            print_err("Trying to use a Mainnet wallet in Stagenet mode!\nConnect to this container and run make_wishlist.py to create a stagenet wallet")
            sys.exit(1)
    #we have to force close the monero rpc because it was launched
    #without tx-notify in make_wishlist
    for proc in psutil.process_iter():
        # check whether the process name matches
        if "-rpc" in proc.name():
            proc.kill()
    fallback_remote_nodes = config["monero"]["fallback_remote_nodes"]
    list_remote_nodes = []
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config["monero"][f"remote_node_{num}"])
    www_root = config["wishlist"]["www_root"]
    remote_node = find_working_node(list_remote_nodes)
    if remote_node:
        start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file)
    else:
        print("No monero remote node")

    #WOW setup
    list_remote_nodes = []
    fallback_remote_nodes = config["wow"]["fallback_remote_nodes"]
    wow_rpc_port = config["wow"]["daemon_port"]
    wow_rpc_url = "http://" + str(local_ip) + ":" + str(rpc_port) + "/json_rpc"
    rpc_bin_file = "/bin/wownero-wallet-rpc"
    list_remote_nodes = []
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config["wow"][f"remote_node_{num}"])
    wow_remote_node = find_working_node(list_remote_nodes)
    if remote_node:
        start_monero_rpc(rpc_bin_file,wow_rpc_port,wow_rpc_url,wow_remote_node,wallet_file,"wow")
    else:
        print("No monero remote node")


    electrum_path = config["btc"]["bin"]
    btc_wallet_path = config["btc"]["wallet_file"]
    bch_wallet_path = config["bch"]["wallet_file"]
    b_rpcuser = config["btc"]["rpcuser"]
    b_rpcpass = config["btc"]["rpcpassword"]
    b_rpcport = config["btc"]["rpcport"]
    if os.environ["waas_mainnet"] == "1":
        if "test" in btc_wallet_path or not bch_wallet_path:
            print_err("You're using a testnet wallet in mainnet mode. Run make_wishlist.py to create mainnet walelts.")
            sys.exit(1)
    electron_path = config["bch"]["bin"]
    
    rpcuser = config["bch"]["rpcuser"]
    rpcpass = config["bch"]["rpcpassword"]
    rpcport = config["bch"]["rpcport"]
    if os.environ["waas_mainnet"] == "1":
        if "test" in bch_wallet_path or not bch_wallet_path:
            print_err("You're using a testnet wallet in mainnet mode. Run make_wishlist.py to create mainnet walelts.")
            sys.exit(1)
    threads = []
    t = threading.Thread(target=start_bit_daemon, args=(electrum_path,btc_wallet_path,b_rpcuser,b_rpcpass,b_rpcport,))
    threads.append(t)
    t = threading.Thread(target=start_bit_daemon, args=(electron_path,bch_wallet_path,rpcuser,rpcpass,rpcport,))
    threads.append(t)
    # Start all threads
    for x in threads:
     x.start()
    # Wait for all of them to finish
    for x in threads:
     x.join()
    http_port = config["callback"]["port"]
    http_server = "http://" + str(local_ip) + ":" + str(http_port)

    wish_list = getJson()

    for wish in wish_list["wishlist"]:
        if wish["btc_address"]:
            address = wish["btc_address"]
            rpc_notify(b_rpcuser,b_rpcpass,b_rpcport,address,http_server)
        if wish["bch_address"]:
            address = wish["bch_address"]
            rpc_notify(rpcuser,rpcpass,rpcport,address,http_server)

    th = threading.Thread(target=refresh_html_loop, args=(remote_node,rpc_url,wow_remote_node,wow_rpc_url,config,))
    th.start()
    th = threading.Thread(target=delete_clicks_db)
    th.start()
    th = threading.Thread(target=save_prices)
    th.start()
    th = threading.Thread(target=refresh_html_loop_1)
    th.start()
    #start the bitcoin listener
    os.system(f'/usr/local/bin/python3 notify_bch_btc.py {http_port}')


def rpc_notify(rpcuser,rpcpass,rpcport,address,callback):
    local_ip = "localhost"
    url = f"http://{rpcuser}:{rpcpass}@{local_ip}:{rpcport}"
    print(url)
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
    pprint.pprint(returnme)

def getPrice(crypto):
    data = cryptocompare.get_price(str(crypto), currency='USD', full=0)
    return(data[str(crypto)]["USD"])

def save_prices():
    while True:
        p_xmr = float(getPrice("XMR"))    
        p_btc = float(getPrice("BTC"))
        p_bch = float(getPrice("BCH"))
        p_wow = float(getPrice("WOW"))

        con = sqlite3.connect('./db/crypto_prices.db')
        cur = con.cursor()
        create_price_table = """ CREATE TABLE IF NOT EXISTS crypto_prices (
                                    data default 0,
                                    xmr integer,
                                    btc integer,
                                    bch integer,
                                    wow integer
                                ); """
        cur.execute(create_price_table)
        
        sql = ''' UPDATE crypto_prices
                  SET xmr = ?,
                      bch = ?,
                      btc = ?,
                      wow =?
                  WHERE data = 0'''   
        cur.execute(sql, (p_xmr,p_bch,p_btc,p_wow))
        con.commit()
        con.close()
        #refresh price on front end
        uid = uuid.uuid4().hex
        asyncio.run(notify_xmr_vps_pi.ws_work_around(uid))
        time.sleep(60*5)

def delete_clicks_db():
    while True:
        #20 clicks/day per ip.
        if os.path.isfile("./db/clicks.db"):
            os.remove("./db/clicks.db")
        time.sleep(60*60*24)

def refresh_html_loop_1():
    while True:
        os.system(f'python3 static/static_html_loop.py')
        time.sleep(5*60)

def local_health_check(wow_xmr,con_local,con_remote,url_remote,config):
    try:
        con_local.store()
        return True
    except Exception as e:
        return False

def remote_health_check(wow_xmr,node,config):
    try:
        info = rpc_connection.get_info()
        if info["status"] != "OK":
            wishlist["metadata"]["status"] = "remote"
            not_ok = 1
            return True
    except:
        return False

def recover_crash(xmr_wow,config,remote_node):
    wishlist["metadata"]["status"] = "remote"
    not_ok = 1
    for proc in psutil.process_iter():
        #kill process
        if f"{wow_xmr}-wallet-rpc" in proc.name():
            proc.kill()

    list_remote_nodes = []
    fallback_remote_nodes = config[xmr_wow]["fallback_remote_nodes"]
    for i in range(int(fallback_remote_nodes)):
        num = (i+1)
        list_remote_nodes.append(config[xmr_wow][f"remote_node_{num}"])

    remote_node = find_working_node(list_remote_nodes)
    if xmr_wow == "monero":
        rpc_bin_file = "/bin/monero-wallet-rpc"
    else:
        rpc_bin_file = "/bin/wownero-wallet-rpc"

    rpc_port = config[xmr_wow]["daemon_port"]
    wallet_file = config[xmr_wow]["wallet_file"]
    rpc_url_local = "http://" + str(localhost) + "/json_rpc"

    if remote_node:
        start_monero_rpc(rpc_bin_file,rpc_port,rpc_url_local,remote_node,wallet_file,xmr_wow)
        wishlist["metadata"]["status"] = "OK"
        return remote_node

def refresh_html_loop(remote_node,local_node,wow_remote_node,wow_local_node,config):
    global www_root
    local_ip = "localhost"
    print(f"remotenode: {remote_node}\n localnode : {local_node}")
    #static html refresh every 5 minutes
    counter = 1
    www_root = config["wishlist"]["www_root"]
    while True: 
        rpc_url = "http://" + str(remote_node) + "/json_rpc"
        wow_rpc_url =  "http://" + str(wow_remote_node) + "/json_rpc"  
        wishlist = getJson()
        node_status = wishlist["metadata"]["monero_status"]
        wow_node_status = wishlist["metadata"]["wownero_status"]
        not_ok = 0
        list_modified = 0

        #each of these could time out
        try:
            rpc_connection = AuthServiceProxy(service_url=rpc_url)
            rpc_local = AuthServiceProxy(service_url=local_node)
        except Exception as e:
            recover_xmr = 1
        try:
            wow_rpc_connection = AuthServiceProxy(service_url=wow_rpc_url)
            wow_rpc_local = AuthServiceProxy(service_url=wow_local_node)
        except:
            recover_wow = 1

        if not remote_health_check("wownero",wow_remote_node,config) or not local_health_check("wownero",wow_rpc_local,wow_rpc_connection,wow_remote_node,config):
            revover_wow = 1
        if not remote_health_check("monero",remote_node,config) or not local_health_check("monero",rpc_local,rpc_connection,remote_node,config):
            recover_xmr = 1
        
        wow_remote_node = recover_crash("wow",config,wow_remote_node)
        remote_node = recover_crash("monero",config,remote_node)
        del rpc_connection
        del rpc_local
        del wow_rpc_local
        del wow_rpc_connection
        time.sleep(60*10)

if __name__ == '__main__':
    config = configparser.ConfigParser()

    config.read('./db/wishlist.ini')
    main(config)


'''
Start the monero daemon with the correct tx-notify file / wallet (from config)
Start the BCH / BTC daemons and set up notifys on each address.
Start listen.py
'''

