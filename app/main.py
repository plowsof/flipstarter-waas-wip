#!/usr/bin/env python
# coding: utf-8
#uvicorn main:app --reload --ssl-keyfile localhost-key.pem --ssl-certfile localhost.pem 

#sqlite3.IntegrityError: UNIQUE constraint failed: donations.donation_address

import configparser
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pprint
from starlette.responses import FileResponse 
import os
from urllib.parse import urlparse, parse_qs
from html import escape
import json
from datetime import datetime
from make_wishlist import create_new_wishlist, put_qr_code, get_unused_address
import sqlite3
import time
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from filelock import FileLock
import math
from start_daemons import main as main_start_daemons

import uvicorn
import threading
# To read your secret credentials
#config = configparser.ConfigParser()
#config.read("config.ini")

wish_config = configparser.ConfigParser()
wish_config.read("./db/wishlist.ini")

#screen -L -Logfile lolokk.txt uvicorn main:app --reload --ssl-keyfile /var/www/letsencrypt/.lego/certificates/rucknium.me.key --ssl-certfile /var/www/letsencrypt/.lego/certificates/rucknium.me.crt
#ssl_certificate ;
#ssl_certificate_key 
app = FastAPI()
app.mount("/flask/static", StaticFiles(directory="static"), name="static")

##
##Ticket price 
ticket_normal = 49.99 #euros
ticket_vip = 99

app.add_middleware(
CORSMiddleware,
allow_origins=["*"], # Allows all origins
allow_credentials=True,
allow_methods=["*"], # Allows all methods
allow_headers=["*"], # Allows all headers
)

@app.get("/flask/", response_class=HTMLResponse)
async def read_root():
    return FileResponse('./static/index.html')

@app.get("/flask/api/timestamp")
async def return_price(status_code=200):
    return db_get_timestamp()

@app.get("/flask/api/price")
async def return_price(status_code=200):
    return db_get_prices()

def db_get_timestamp():
    con = sqlite3.connect('./db/modified.db')
    cur = con.cursor()
    create_modified_table = """ CREATE TABLE IF NOT EXISTS modified (
                                data integer default 0,
                                comment integer default 1,
                                wishlist integer default 1
                            ); """
    cur.execute(create_modified_table)
    cur.execute('SELECT * FROM modified where data = 0')
    rows = cur.fetchall()
    pprint.pprint(rows)
    return_me = {
    "comments": rows[0][1],
    "wishlist": rows[0][2]
    }
    con.commit()
    con.close()
    return return_me

def db_get_prices():
    con = sqlite3.connect('./db/crypto_prices.db')
    cur = con.cursor()
    create_price_table = """ CREATE TABLE IF NOT EXISTS crypto_prices (
                                data default 0,
                                xmr integer,
                                btc integer,
                                bch integer
                            ); """
    cur.execute(create_price_table)
    cur.execute('SELECT * FROM crypto_prices WHERE data = ?',[0])
    rows = cur.fetchall()
    return_me = {
    "bitcoin-cash": rows[0][3],
    "monero": rows[0][1],
    "bitcoin": rows[0][2]
    }
    con.close()
    return return_me

@app.post("/flask/crypto_donate")
async def handle_crypto_form(request: Request):
    global wish_config, ticket_normal, ticket_vip
    body = await request.body()
    #b'amount=1&coins=xmr&choice=tax&fname=&fname=&street=&zip=&email=&rfund='
    #pprint.pprint(body)
    client_host = request.client.host
    print(client_host)
    print("hello world")
    try:
        client_address = request.client.host
        print(client_address)
        vals = parse_qs(body)

        for x in vals:
            try:
                escape(vals[x][0].decode("utf-8"))
                pass
            except Exception as e:
                print("fix the problem?")
                vals[x] = [b'']

        comment = null_if_not_exists(vals,b"comment")
        comment_name = null_if_not_exists(vals,b"comment_name")
        if len(comment) > 140 or len(comment_name) > 12:
            return   
        #vals[b'uid'][0] = wish id
        #20 clicks per day per ip...
        if not clicks_today(client_address):
            print("Rejected")
            return
        #add into database? a thread to remove in 15 mins? hm
        pprint.pprint(vals)
        print(f"the choise is {vals[b'choice'][0]}")
        if vals[b'choice'][0] == b'tax':
            #database entry
            #tax receipt
            #send_email(send_to,address,amount)
            the_email = null_if_not_exists(vals,b"email")
            #if not valid_email(the_email):
            #    return
            #print(f"we chose: {vals[b'coins'][0]}")
            valid_coin = 0
            ticker =  null_if_not_exists(vals,b"coins")
            if ticker == "xmr":
                valid_coin = 1
            if ticker == "bch":
                valid_coin = 1
            if ticker == "btc":
                valid_coin = 1

            if valid_coin == 0:
                return

            address = get_unused_address(wish_config,ticker)
            #does there need to be a time contraint on when donations can receive a receipt?
            #or they can only be used once?

            price_ticker = ""
            ticket_valid = 1
            expected = 0
            wish_id = null_if_not_exists(vals,b"uid")
            #enforce ticker symbols
            
            ticket_amount = null_if_not_exists(vals,b'quantity')

            if ticker == "xmr":
                ticker = "monero"
            elif ticker == "bch":
                ticker = "bitcoin-cash"
            elif ticker == "btc":
                ticker = "bitcoin"
            else:
                ticket_valid = 0

            try:
                if ticket_amount == "":
                    ticket_valid = 0
                elif int(ticket_amount) >= 1:
                    ticket_amount = math.ceil(int(ticket_amount))
                else:
                    ticket_valid = 0
            except Exception as e:
                print(e)
                ticket_valid = 0


            if wish_id == "ticket":
                #ticket
                ticket_price = ticket_normal
            elif wish_id == "ticket_vip":
                #vip
                ticket_price = ticket_vip
            else:
                ticket_valid = 0

            if ticket_valid == 1:
                crypto_price = db_get_prices()[ticker]
                print(f"crypto price = {crypto_price}")
                ticket_total = ticket_price * ticket_amount
                print(f"ticket total = {ticket_total}")
                expected = round((ticket_total / crypto_price),12)
            else:
                print("error ticket_valid = 0")

            print(f"the donation address is {address}")
            weird = null_if_not_exists(vals,b"comment")
            print(f"the comment is {weird}")
            db_data = {
            "email": null_if_not_exists(vals,b"email"),
            #the amount selected by the form is meaningless
            #we only care about what gets deposited at the end
            #"amount": null_if_not_exists(vals,b"amount"),
            "amount": 0,
            "fname": null_if_not_exists(vals,b"fname"),
            "donation_address": address,
            "zipcode": null_if_not_exists(vals,b"zip"),
            "address": null_if_not_exists(vals,b"street"),
            "date_time": datetime.now(),
            "refund_address": null_if_not_exists(vals,b"rfund"),
            "crypto_ticker": null_if_not_exists(vals,b"coins"),
            "wish_id": null_if_not_exists(vals,b"uid"),
            "comment": comment,
            "comment_name": comment_name,
            "amount_expected": expected,
            "consent": null_if_not_exists(vals,b"consent"),
            "quantity": ticket_amount,
            "type": wish_id
            }
            db_receipts_add(db_data)
            info = {
            "address": address,
            "amount_expected": expected
            }
            pprint.pprint(vals)
            pprint.pprint(db_data)
            test = json.dumps(info)  
            return JSONResponse(content=test)

    except Exception as e:
        raise e

def null_if_not_exists(vals,index):
    try:
        if index == b"comment":
            return escape(vals[index][0].decode("utf-8"))
        else:
            return escape(vals[index][0].decode("utf-8"))
        pass
    except Exception as e:
        return ""

def clicks_today(client_ip):
    con = sqlite3.connect('./db/clicks.db')
    cur = con.cursor()
    create_clicks_table = """ CREATE TABLE IF NOT EXISTS clicks (
                                clicks integer default 0 not null,
                                ip text PRIMARY KEY,
                                time_last integer default 0
                            ); """

    cur.execute(create_clicks_table)
    con.commit()
    cur.execute('SELECT * FROM clicks WHERE ip = ?',[client_ip])
    rows = cur.fetchall()
    if len(rows) == 0:
        #we didnt click today
        #insert into db then return true
        sql = ''' INSERT INTO clicks (ip,clicks,time_last)
                  VALUES(?,?,?) '''
        cur.execute(sql, (client_ip,1,time.time()))
        con.commit()
        return True

    if rows[0][0] > 19:
        return False
    if (int(time.time()) - int(rows[0][2])) < 1:
        #1 click per second per ip 
        return
    else:
        print(f"time since last click = {(int(time.time()) - int(rows[0][2]))}")
        clicks = rows[0][0]
        clicks +=  1
        print(f"clicks={clicks}")
        sql = ''' UPDATE clicks
                  SET clicks = ?, 
                  time_last = ?
                  WHERE ip = ?'''   
        cur.execute(sql, (clicks,int(time.time()),client_ip))
        con.commit()
        return True

def logit(s):
    try:
        with open("logged.text", "a+") as f:
            f.write(pprint.pprint(s))
            pass
    except Exception as e:
        raise e

def db_receipts_add(data):
    con = sqlite3.connect('./db/receipts.db')
    cur = con.cursor()
    sql = ''' INSERT INTO donations (email,amount,fname,donation_address,zipcode,address,date_time,refund_address,crypto_ticker,wish_id,comment,comment_name,amount_expected,consent,quantity,type)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur.execute(sql, (data["email"],data["amount"],data["fname"],data["donation_address"],data["zipcode"],data["address"],data["date_time"],data["refund_address"],data["crypto_ticker"],data["wish_id"],data["comment"],data["comment_name"],data["amount_expected"],data["consent"],data["quantity"],data["type"]))
    con.commit()

if __name__ == "__main__":
    #if wishlist file exists - assume we can start_daemons
    if os.path.isfile("./static/data/wishlist-data.json"):        
        th = threading.Thread(target=main_start_daemons, args=(wish_config,))
        th.start()
    else:
        print("Run make_wishlist.py")
    #ssl certs should be in ./ssl folder 
    if os.path.isfile("./ssl/privkey.pem") and os.path.isfile("./ssl/fullchain.pem"):
        uvicorn.run("main:app", port=8000, host="0.0.0.0", key_file="privkey.pem", ssl_certificate="fullchain.pem", reload=True)
        #fullchain.pem  privkey.pem
        #sudo screen -L -Logfile--ssl-keyfile rurucknium.me.crt sudo screen -L -Logfile uvicorn-output.txt uvicorn main:app --reload --ssl-keyfile rucknium.me.key --ssl-certfile rucknium.me.crt
    else:
        print("Defaulting to http: place privkey.pem and fullchain.pem in ./ssl folder and restart for https")
        uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
    #if wishilist has been created. start 'start_daemons.py' too