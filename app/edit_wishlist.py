import configparser
import json
#address_create_notify == get btc or bch address
from make_wishlist import create_new_wishlist, address_create_notify, get_xmr_subaddress, put_qr_code, get_unused_address
import pprint
import os 
import sys
from filelock import FileLock
from datetime import datetime
from rss_feed import add_to_rfeed
config = ""

def main():
    global config
    print('''Wishlist editor.
        this script assumes that your wishlist is running already.
        Lets begin!''')
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    if not os.path.isfile("./db/your_wishlist.json"):
        print("Error: please run make_wishlist.py first.")
        sys.exit(1)

    with open("./db/your_wishlist.json", "r") as f:
        wishlist = json.load(f)
    if not wishlist["wishlist"]:
        print("Empty wishlist detected. Please add a wish")
        wish_prompt(config)
        return

    #for i in range(len(wishlist["wishlist"])):
    #    print(f"{i}) {wishlist['wishlist'][i]['title']}")
    print("1) Add a wish")
    print("2) Remove")
    print("3) Edit")
    answer = ""
    while answer not in [1,2,3]:
        answer = int(input("Enter 1 2 or 3 >> "))
    if answer == 1:
        wish_prompt(config)
    if answer == 2:
        wish_edit(wishlist,"Delete",config["wishlist"]["www_root"])
    if answer == 3:
        wish_edit(wishlist,"Edit",config["wishlist"]["www_root"])

#find the matching wish and set the variables
def wish_edit(wishlist,edit_delete,www_root):
    returned_list = {"hello":"world"}
    print(f"Which wish would you like to {edit_delete}")
    for i in range(len(wishlist["wishlist"])):
        offset = i 
        offset += 1
        print(f"{offset}) {wishlist['wishlist'][i]['title']}")
    index = ""
    end = len(wishlist["wishlist"])
    end += 1
    print(f"end: {end}")
    while index not in range(1,end):
        index = int(input(f"Pick a wish to Edit / Remove (1-{offset}) >> "))

    index -= 1
    if edit_delete == "Edit":
        while True:
            print("EDIT")
            #title
            print(f"Edit Wish: {wishlist['wishlist'][index]['title']}")
            print("1) Title")
            print("2) Goal")
            print("3) Description")
            print("4) Add monthly fee (e.g. -$100 / month")
            answer = ""
            goal = ""
            description = ""
            cost = ""
            title = ""
            while answer not in [1,2,3,4]:
                answer = int(input(">> "))
            if answer == 1:
                wishlist["wishlist"][index]["title"] = input("New title >> ")
            if answer == 2:
                while not goal.isnumeric():
                    goal = input("New $Goal >> ")
                wishlist["wishlist"][index]["goal_usd"] = goal
            if answer == 3:
                wishlist["wishlist"][index]["description"] = input("New Description >> ")
            if answer == 4:
                while not cost.isnumeric():
                    cost = input("Cost of the recurring amount in USD e.g. 100 >> ")
                wishlist["wishlist"][index]["type"] = "recurring:" + str(cost)
                pprint.pprint(wishlist["wishlist"][index])
                wish_id = wishlist["wishlist"][index]["xmr_address"][0:12]
                add_to_cron(wish_id)
            again = 0
            finish = ""
            while finish.lower() not in ["y","yes","no","n"]:
                finish = input("Edit this wish again? y/n >> ")
            if "n" in finish.lower():
                print("saving edits")
                data_json = os.path.join(www_root,"data","wishlist-data.json")
                with open(data_json,"r") as f:
                    now_wishlist = json.load(f)
                for i in range(len(now_wishlist["wishlist"])):
                    if now_wishlist["wishlist"][i]["xmr_address"] == wishlist["wishlist"][index]["xmr_address"]:
                        now_wishlist["wishlist"][i]["goal_usd"] = wishlist["wishlist"][index]["goal_usd"]
                        now_wishlist["wishlist"][i]["title"] = wishlist["wishlist"][index]["title"]
                        now_wishlist["wishlist"][i]["description"] = wishlist["wishlist"][index]["description"]
                        now_wishlist["wishlist"][i]["type"] = wishlist["wishlist"][index]["type"]
                        break
                lock = FileLock(f"{data_json}.lock")
                with lock:
                    with open(data_json, "w+") as f:
                        json.dump(now_wishlist, f, indent=2) 
                break
    if edit_delete == "Delete":
        while True:
            answer = input(f"Delete: {wishlist['wishlist'][i]['title']} \n Are you sure?")
            if "y" in answer.lower():
                wishlist = delete_wish(wishlist,index)
                break
    pprint.pprint(wishlist)
    with open("./db/your_wishlist.json","w") as f:
        json.dump(wishlist,f, indent=6)

def add_to_cron(wish_id):
    os.system(f"(crontab -u $(whoami) -l; echo '0 0 1 * * (cd /home/app && /usr/local/bin/python3 wishlist_recurring.py {wish_id})' ) | crontab -u $(whoami) -")
    print("Added recurring payment to happen on the 1st day of each month")

#tidy this up
def delete_wish(wishlist,index):
    global config
    deleted = wishlist["wishlist"][index]
    www_root = config["wishlist"]["www_root"]
    data_json = os.path.join(www_root,"data","wishlist-data.json")
    with open(data_json,"r") as f:
        now_wishlist = json.load(f)
    for i in range(len(now_wishlist["wishlist"])):
        if now_wishlist["wishlist"][i]["xmr_address"] == deleted["xmr_address"]:
            archive = now_wishlist["wishlist"][i]
            now_wishlist["wishlist"].pop(i)
            break
    now_wishlist["archive"].append(archive)
    lock = FileLock(f"{data_json}.lock")
    with lock:
        with open(data_json, "w+") as f:
            json.dump(now_wishlist, f, indent=2) 
    wishlist["wishlist"].pop(index)
    with open('./db/your_wishlist.json','w+') as f:
        json.dump(wishlist, f, indent=6)
    return wishlist
    #lets find the wish in our data.json file in www_root 

#add 1 wish without deleting the current data.
#create qrs for the new wish
def wish_add(wish,config):
    local_ip = "localhost"
    try:
        if os.path.isfile("./db/your_wishlist.json"):
            print("why")
            with open('./db/your_wishlist.json', "r") as f:
                wishlist = json.load(f)
        else:
            wishlist = {}
            wishlist["wishlist"] = []
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
        bin_dir = config["bch"]["bin"]
        port = config["callback"]["port"]
        wallet_path = config["bch"]["wallet_file"]
        print(f'the port is {port}')
        new_wish["bch_address"] = get_unused_address(config,"bch")
        put_qr_code(new_wish["bch_address"], "bch")
        bin_dir = config["btc"]["bin"]
        wallet_path = config["btc"]["wallet_file"]
        new_wish["btc_address"] = get_unused_address(config,"btc")
        put_qr_code(new_wish["btc_address"], "btc")
        rpc_port = config["monero"]["daemon_port"]
        if rpc_port == "":
            rpc_port = 18082
        rpc_url = "http://" + str(local_ip) + ":" + str(rpc_port) + "/json_rpc"
        wallet_path = os.path.basename(config['monero']['wallet_file'])
        new_wish["xmr_address"] = get_unused_address(config,"xmr")
        put_qr_code(new_wish["xmr_address"], "xmr")
        new_wish = new_wish.copy()
        wishlist["wishlist"].append(new_wish)
        with open('./db/your_wishlist.json','w+') as f:
            json.dump(wishlist, f,indent=6)

        orig_goal = wish["goal"]
        percent = int(config["wishlist"]["percent_buffer"]) / 100
        percent = float(percent) * int(orig_goal)
        goal = int(orig_goal) + int(percent)

        new_wish = { 
                    "goal_usd":int(wish["goal"]), #these will be in usd
                    "usd_total":0, #usd - if you cash out for stability
                    "contributors":0,
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
        www_root = config["wishlist"]["www_root"]
        data_json = os.path.join(www_root,"data","wishlist-data.json")
        with open(data_json,"r") as f:
            now_wishlist = json.load(f)
        now_wishlist["wishlist"].append(new_wish)
        lock = FileLock(f"{data_json}.lock")
        with lock:
            with open(data_json, "w+") as f:
                json.dump(now_wishlist, f, indent=2) 
        pass
    except Exception as e:
        raise e

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

main()