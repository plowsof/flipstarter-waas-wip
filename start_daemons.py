import os
import json
import requests
import configparser
import subprocess
import time
import sys
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException

wallet_dir = os.path.join(os.path.abspath(os.path.join(os.getcwd(),"wallets")))

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

def moenro_rpc_open_wallet(rpc_url,wallet_file):
    rpc_connection = AuthServiceProxy(service_url=rpc_url)
    try:
        wallet_fname = os.path.basename(wallet_file)
        info = rpc_connection.open_wallet({"filename": wallet_fname})
        pass
    except Exception as e:
        print(e)
        sys.exit(1)
def start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file=None):
    global wallet_dir
    os.path.join(os.path.abspath(os.path.join(os.getcwd(),"xmr-btc-wishlist.py")))
    print(f"{wallet_file}")
    print(f"{rpc_port}")
    print(f"{os.path.join(os.path.abspath(os.path.join(os.getcwd(),'xmr-btc-wishlist.py')))}")
    rpc_args = [ 
        f"{rpc_bin_file}", 
        "--wallet-dir", wallet_dir,
        "--rpc-bind-port", rpc_port,
        "--disable-rpc-login",
        "--tx-notify", f"python3 {os.path.join(os.path.abspath(os.path.join(os.getcwd(),'xmr_in_vps_pi.py')))} %s",
        "--daemon-address", remote_node,
        "--stagenet"
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
        time.sleep(1)
    if kill_daemon == 1:
        print(line.rstrip())
        monero_daemon.terminate()
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
            wallet_fname = os.path.basename(wallet_file)
            info = rpc_connection.open_wallet({"filename": wallet_fname})
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
    with open("wishlist-data.json", "r") as f:
        return json.load(f)

def start_bch_daemon(electron_bin,wallet_file):
    run_args = [
    electron_bin, "daemon", "stop", "--testnet"
    ]
    print(run_args)
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()
    run_args = [
    electron_bin, "daemon", "start", "load_wallet", "-w", wallet_file, "--testnet"
    ]
    print(run_args)
    bch_daemon = subprocess.Popen(run_args)
    bch_daemon.communicate()

def start_btc_daemon(electrum_bin,wallet_file):
    run_args = [
    electrum_bin, "stop", "--testnet"
    ]
    btc_daemon = subprocess.Popen(run_args, stdout=subprocess.PIPE)
    btc_daemon.communicate()
    run_args = [
    electrum_bin, "daemon", "-d", "--testnet"
    ]
    btc_daemon = subprocess.Popen(run_args, stdout=subprocess.PIPE)
    btc_daemon.communicate()
    stream = os.popen(f"{electrum_bin} load_wallet -w {wallet_file} --testnet")
    stream.read()


def main(config):
    rpc_bin_file = os.path.join(".", "bin", "monero-wallet-rpc")
    rpc_port = config["monero"]["daemon_port"]
    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
    wallet_file = config["monero"]["wallet_file"]
    remote_node = config["monero"]["remote_node"]
    if monero_rpc_online(rpc_url) == True:
        monero_rpc_close_wallet(rpc_url)
        moenro_rpc_open_wallet(rpc_url,wallet_file)
    else:
        start_monero_rpc(rpc_bin_file,rpc_port,rpc_url,remote_node,wallet_file)

    electrum_path = config["btc"]["bin"]
    btc_wallet_path = config["btc"]["wallet_file"]
    start_btc_daemon(electrum_path,btc_wallet_path)

    electron_path = config["bch"]["bin"]
    bch_wallet_path = config["bch"]["wallet_file"]
    start_bch_daemon(electron_path,bch_wallet_path)
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


    #start the bitcoin listener
    os.system(f'python3 listen.py {http_port}')


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    main(config)


'''
Start the monero daemon with the correct tx-notify file / wallet (from config)
Start the BCH / BTC daemons and set up notifys on each address.
Start listen.py
'''