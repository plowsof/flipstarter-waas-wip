import configparser
import json
#address_create_notify == get btc or bch address
import pprint
import os 
import sys
from filelock import FileLock
from datetime import datetime
from rss_feed import add_to_rfeed
import time
from helper_create import wish_prompt
config = ""
sys.path.insert(1, './static/')
from static_html_loop import main as static_main
import sqlite3

def main():
    global config
    print('''Wishlist editor.
        this script assumes that your wishlist is running already.
        Lets begin!''')
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    if not os.path.isfile("./static/data/wishlist-data.json"):
        print("Error: please run make_wishlist.py first.")
        sys.exit(1)

    with open("./static/data/wishlist-data.json", "r") as f:
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

    #blindly trigger a static html refresh
    static_main(config)

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
    while index not in range(1,end):
        index = int(input(f"Pick a wish to Edit (1-{offset}) >> "))

    index -= 1
    if edit_delete == "Edit":
        while True:
            #title
            print(f"Edit Wish: {wishlist['wishlist'][index]['title']}")
            print("1) Title")
            print("2) Goal")
            print("3) Description")
            print("4) Add monthly fee (e.g. -$100 / month")
            print("5) Status (WIP / RELEASED)")
            print("6) Totals")
            answer = ""
            goal = ""
            description = ""
            cost = ""
            title = ""
            while answer not in [1,2,3,4,5,6]:
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
                #pprint.pprint(wishlist["wishlist"][index])
                wish_id = wishlist["wishlist"][index]["xmr_address"][0:12]
                insert_recurring(wish_id)
            if answer == 5:
                wishlist["wishlist"][index]["status"] = input("New Status >> ")
            if answer == 6:
                total_xmr = wishlist["wishlist"][index]["xmr_total"]
                total_bch = wishlist["wishlist"][index]["bch_total"]
                total_btc = wishlist["wishlist"][index]["btc_total"]
                total_usd = wishlist["wishlist"][index]["usd_total"]
                goal = wishlist["wishlist"][index]["goal_usd"]
                choice = {"1": "xmr", "2": "bch", "3": "btc", "4": "usd"}
                print("Coin [total]")
                print(f"1) XMR [{total_xmr}]")
                print(f"2) BCH [{total_bch}]")
                print(f"3) BTC [{total_btc}]")
                print(f"4) USD [{total_usd}]")
                print(f"5) 'Cash out' - Zero totals and set USD to [{goal}].")
                while answer not in [1,2,3,4,5]:
                    answer = float(input(">> "))
                if answer != 5:
                    coin = choice[str(answer)]
                    while True:
                        try:
                            userInput = input(f"Enter the new total for {coin}\n>>")
                            val = float(userInput)
                            break
                        except ValueError:
                            print("That's not an int!")
                    wishlist["wishlist"][index][f"{coin}_total"] = val
                else:
                    #zero values
                    for x in choice:
                        coin = choice[x]
                        wishlist["wishlist"][index][f"{coin}_total"] = 0
                    wishlist["wishlist"][index]["usd_total"] = goal

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
                        now_wishlist["wishlist"][i]["status"] = wishlist["wishlist"][index]["status"]
                        now_wishlist["wishlist"][i]["xmr_total"] = wishlist["wishlist"][index]["xmr_total"]
                        now_wishlist["wishlist"][i]["xmr_total"] = wishlist["wishlist"][index]["bch_total"]
                        now_wishlist["wishlist"][i]["btc_total"] = wishlist["wishlist"][index]["btc_total"]
                        now_wishlist["wishlist"][i]["usd_total"] = wishlist["wishlist"][index]["usd_total"]
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
    #pprint.pprint(wishlist)
    with open("./static/data/wishlist-data.json","w") as f:
        json.dump(wishlist,f, indent=6)

def insert_recurring(wish_id):
    con = sqlite3.connect('./db/recurring_fees.db')
    cur = con.cursor()
    create_fees_table = """ CREATE TABLE IF NOT EXISTS fees (
                                wish_id text PRIMARY KEY
                            ); """

    cur.execute(create_fees_table)
    cur.execute('SELECT * FROM fees WHERE wish_id = ?',[wish_id])
    rows = cur.fetchall()
    #insert if not in db already
    if not len(rows):
        cur.execute('INSERT INTO fees VALUES(?)',[wish_id])
        con.commit()
    con.close()

#tidy this up
def delete_wish(wishlist,index):
    global config
    deleted = wishlist["wishlist"][index]
    www_root = config["wishlist"]["www_root"]
    now_wishlist = wishlist
    for i in range(len(now_wishlist["wishlist"])):
        if now_wishlist["wishlist"][i]["xmr_address"] == deleted["xmr_address"]:
            archive = now_wishlist["wishlist"][i]
            now_wishlist["wishlist"].pop(i)
            break
    now_wishlist["archive"].append(archive)
    data_json = './static/data/wishlist-data.json'
    lock = FileLock(f"{data_json}.lock")
    with lock:
        with open(data_json, "w+") as f:
            json.dump(now_wishlist, f, indent=2) 
    con = sqlite3.connect('./db/recurring_fees.db')
    cur = con.cursor()
    wish_id = deleted["id"]
    cur.execute('DELETE FROM fees WHERE wish_id=?',[wish_id])
    con.commit()
    con.close()
    return now_wishlist
    #lets find the wish in our data.json file in www_root 

main()