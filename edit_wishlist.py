import configparser
import json
from make_wishlist import create_new_wishlist, address_create_notify, get_xmr_subaddress
import pprint
import os 
def main():
    print('''Wishlist editor.
        this script assumes that your wishlist is running already.
        Lets begin!''')
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    with open("your_wishlist.json", "r") as f:
        wishlist = json.load(f)
    #for i in range(len(wishlist["wishlist"])):
    #    print(f"{i}) {wishlist['wishlist'][i]['title']}")
    print("1) Add a wish")
    print("2) Remove/edit a wish")
    while True:
        try:
            answer = input("[Enter 1 or 2] >> ")
            print(answer)
            if answer == "1":
                #add
                wish_prompt(config)
                print("prompt")
                break
            else:
                print("Not == 1")
                if answer == "2":
                    break
        except Exception as e:
            pass

def wish_add(wish,config):
    try:
        if os.path.isfile("your_wishlist.json"):
            print("why")
            with open('your_wishlist.json', "r") as f:
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
        bin_dir = config["bch"]["bin"]
        port = config["callback"]
        wish["bch_address"] = address_create_notify(bin_dir,port,addr="",create=1,notify=1)
        bin_dir = config["btc"]["bin"]
        wish["btc_address"] = address_create_notify(bin_dir,port,="",create=1,notify=1)
        rpc_port = config["monero"]["daemon_port"]
        if rpc_port == "":
            rpc_port = 18082
        rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
        wish["xmr_address"] = get_xmr_subaddress(rpc_url,config["monero"]["wallet_path"],wish["title"]):
        wish = wish.copy()
        wishlist["wishlist"].append(wish)
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
    else:
        print("Wishlist created, lets add donation addresses to them..")
    


main()