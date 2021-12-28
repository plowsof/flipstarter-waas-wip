import configparser
import json
from make_wishlist import create_new_wishlist, address_create_notify, get_xmr_subaddress
import pprint
import os 
import sys
config = ""

def main():
    global config
    print('''Wishlist editor.
        this script assumes that your wishlist is running already.
        Lets begin!''')
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    if not os.path.isfile("your_wishlist.json"):
        print("Error: please run make_wishlist.py first.")
        sys.exit(1)

    with open("your_wishlist.json", "r") as f:
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
        wish_edit(wishlist,"Delete")
    if answer == 3:
        wish_edit(wishlist,"Edit")

def wish_edit(wishlist,edit_delete):
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
            answer = ""
            goal = ""
            description = ""
            title = ""
            while answer not in [1,2,3]:
                answer = int(input(">> "))
            if answer == 1:
                wishlist["wishlist"][index]["title"] = input("New title >> ")
            if answer == 2:
                while not goal.isnumeric():
                    goal = input("New $Goal >> ")
                wishlist["wishlist"][index]["goal_usd"] = goal
            if answer == 3:
                wishlist["wishlist"][index]["description"] = input("New Description >> ")
            again = 0
            finish = ""
            while finish.lower() not in ["y","yes","no","n"]:
                finish = input("Edit this wish again? y/n >> ")
            if "n" in finish.lower():
                print("saving edits")
                pprint.pprint(wishlist)
                break
    if edit_delete == "Delete":
        while True:
            answer = input(f"Delete: {wishlist['wishlist'][i]['title']} \n Are you sure?")
            if "y" in answer.lower():
                wishlist = delete_wish(wishlist,index)
                break
    pprint.pprint(wishlist)
    with open("your_wishlist.json","w") as f:
        json.dump(wishlist,f, indent=6)
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
    wishlist["wishlist"].pop(index)
    with open('your_wishlist.json','w+') as f:
        json.dump(wishlist, f, indent=6)
    now_wishlist["archive"].append(archive)
    return wishlist
    #lets find the wish in our data.json file in www_root 

def wish_add(wish,config):
    try:
        if os.path.isfile("your_wishlist.json"):
            print("why")
            with open('your_wishlist.json', "r") as f:
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
        bin_dir = config["bch"]["bin"]
        port = config["callback"]["port"]
        wallet_path = config["bch"]["wallet_file"]
        print(f'the port is {port}')
        new_wish["bch_address"] = address_create_notify(bin_dir,wallet_path,port,addr="",create=1,notify=1)
        bin_dir = config["btc"]["bin"]
        wallet_path = config["btc"]["wallet_file"]
        new_wish["btc_address"] = address_create_notify(bin_dir,wallet_path,port,addr="",create=1,notify=1)
        rpc_port = config["monero"]["daemon_port"]
        if rpc_port == "":
            rpc_port = 18082
        rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
        wallet_path = os.path.basename(config['monero']['wallet_file'])
        new_wish["xmr_address"] = get_xmr_subaddress(rpc_url,wallet_path,wish["title"])
        new_wish = new_wish.copy()
        wishlist["wishlist"].append(new_wish)
        with open('your_wishlist.json','w+') as f:
            json.dump(wishlist, f,indent=6)
        print("CREATE WISHLIST")
        create_new_wishlist()
        pass
    except Exception as e:
        raise e


def wish_prompt(config):
    wish={}
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
        wish_prompt()
    


main()