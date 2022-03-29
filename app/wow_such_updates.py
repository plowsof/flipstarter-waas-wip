#update v1.0 user to the WOWnero version
'''
[wow]
wallet_file = 
bin = bin/wownero-wallet-rpc
daemon_port = 15112
'''
import setup_wallets
import start_daemons
import configparser 
import helper_create
import os 
import pprint
import json

wownero_wallet_rpc = "bin/wownero-wallet-rpc"
config = configparser.ConfigParser()
config.read('./db/wishlist.ini')
config["wow"]["daemon_port"] = "15112"
config["wow"]["bin"] = "bin/wownero-wallet-rpc"
with open('./db/wishlist.ini', 'w') as configfile:
    config.write(configfile)
list_remote_nodes = []
fallback_remote_nodes = config["wow"]["fallback_remote_nodes"]
for i in range(int(fallback_remote_nodes)):
    num = (i+1)
    list_remote_nodes.append(config["wow"][f"remote_node_{num}"])

wow_remote_node = "http://" + str(start_daemons.find_working_node(list_remote_nodes,"wow"))
if not wow_remote_node:
    print_err("Error Wownero remote unreachable")
    sys.exit(1)

#create wallet starts the rpc 
setup_wallets.create_monero_wallet(config,wow_remote_node,"wow")
config = configparser.ConfigParser()
config.read('./db/wishlist.ini')
wallet_file = config["wow"]["wallet_file"]
rpc_url = "http://localhost:15112/json_rpc"

with open("./static/data/wishlist-data.json", "r") as f:
    wishlist = json.load(f)

for i in range(len(wishlist["wishlist"])):
	wish = wishlist["wishlist"][i]
	wish["wow_total"] = 0
	wish["wow_history"] = []
	wish["wow_address"] = helper_create.get_unused_address(config,"wow",title=None)
	wish["qr_img_url_wow"] = f"static/images/{wish['wow_address'][0:12]}.png"
	helper_create.put_qr_code(wish["wow_address"], "wow")
	wishlist["wishlist"][i] = wish

wishlist["metadata"]["wow_total"] = 0
wishlist["metadata"]["wownero_status"] = "OK"
wishlist["metadata"]["monero_status"] = "OK"
with open("./static/data/wishlist-data.json", "w") as f:
    json.dump(wishlist, f, indent=6) 

#delete the prices database, so a fresh one is created with a 'wow' column
os.remove('db/crypto_prices')

input("Press Enter to clear the console (last chance to write your seeds down!")
os.system("clear")
setup_wallets.print_msg("Finished. Run edit_wishlist.py to add/edit wishes. Goodluck!")
setup_wallets.print_msg("Access your page locally @ 172.20.111.2:8000/donate")

#clear memory cache (linux)
try:
    os.system('sync')
    open('/writable_proc/sys/vm/drop_caches','w').write("1\n")
except:
    pass
#> > /dev/null 2>&1 &'
os.system('nohup python3 start_daemons.py &')