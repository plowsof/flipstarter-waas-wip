#!/usr/bin/env python
# coding: utf-8
#uvicorn main:app --reload --ssl-keyfile localhost-key.pem --ssl-certfile localhost.pem 

#FORM
'''
DONATE - RECEIPT YES / NO?
'''
#sqlite3.IntegrityError: UNIQUE constraint failed: donations.donation_address

import configparser
import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pprint
from starlette.responses import FileResponse 
import os
from urllib.parse import urlparse, parse_qs
from html import escape
import json
from datetime import datetime
from make_wishlist import create_new_wishlist, address_create_notify, get_xmr_subaddress, put_qr_code
import smtplib
from email.utils import parseaddr
import re
import sqlite3
from datetime import datetime
import time
from fastapi.responses import JSONResponse
import uuid
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
import hmac,base64
from filelock import FileLock
import math

import random
import requests



# To read your secret credentials
config = configparser.ConfigParser()
config.read("config.ini")

wish_config = configparser.ConfigParser()
wish_config.read("wishlist.ini")



class Webhook(BaseModel):
    merchant_id: str

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
    return FileResponse('index.html')

@app.get("/flask/api/timestamp")
async def return_price(status_code=200):
    return db_get_timestamp()

@app.get("/flask/api/price")
async def return_price(status_code=200):
    return db_get_prices()

def db_get_timestamp():
    con = sqlite3.connect('modified.db')
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
    con = sqlite3.connect('crypto_prices.db')
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
    config = configparser.ConfigParser()
    config.read("wishlist.ini")
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
            while True:
                #print(f"we chose: {vals[b'coins'][0]}")
                valid_coin = 0
                if vals[b'coins'][0] == b"xmr":
                    rpc_port = wish_config["monero"]["daemon_port"]
                    rpc_url = "http://localhost:" + str(rpc_port) + "/json_rpc"
                    wallet_path = os.path.basename(wish_config['monero']['wallet_file'])
                    address = get_xmr_subaddress(rpc_url,wallet_path,"An address label")
                    valid_coin = 1
                    #notify qzr3duvhlknh9we5g8x3wvkj5qvh625tzv36ye9kwl http://localhost:12347 --testnet
                    print(f"the address is: {address}")

                if vals[b'coins'][0] == b"bch":
                    wallet_path = wish_config["bch"]["wallet_file"]
                    bin_dir = wish_config["bch"]["bin"]
                    port = wish_config["callback"]["port"]
                    rpcuser = config["bch"]["rpcuser"]
                    rpcpass = config["bch"]["rpcpassword"]
                    rpcport = config["bch"]["rpcport"]
                    address = address_create_notify(bin_dir,wallet_path,port,"",1,1,rpcuser,rpcpass,rpcport)
                    valid_coin = 1
                if vals[b'coins'][0] == b"btc":
                    wallet_path = wish_config["btc"]["wallet_file"]
                    bin_dir = wish_config["btc"]["bin"]
                    port = wish_config["callback"]["port"]
                    rpcuser = config["btc"]["rpcuser"]
                    rpcpass = config["btc"]["rpcpassword"]
                    rpcport = config["btc"]["rpcport"]
                    address = address_create_notify(bin_dir,wallet_path,port,"",1,1,rpcuser,rpcpass,rpcport)
                    valid_coin = 1

                pprint.pprint(address)
                if "not" in address:
                    return
                if valid_coin == 0:
                    return

                con = sqlite3.connect('receipts.db')
                cur = con.cursor()
                create_receipts_table = """ CREATE TABLE IF NOT EXISTS donations (
                                            email text,
                                            amount integer default 0 not null,
                                            fname text,
                                            donation_address text PRIMARY KEY,
                                            zipcode text,
                                            address text,
                                            date_time text,
                                            refund_address text,
                                            crypto_ticker text,
                                            wish_id text,
                                            comment text,
                                            comment_name text,
                                            amount_expected integer default 0 not null,
                                            consent integer default 0,
                                            quantity integer default 0,
                                            type text,
                                            comment_bc integer default 0
                                        ); """

                cur.execute(create_receipts_table)
                con.commit()
                cur.execute('SELECT * FROM donations WHERE address = ?',[address])
                rows = len(cur.fetchall())
                pprint.pprint(cur.fetchall())
                #its a used address. continue loop
                if rows == 0:
                    break

            #does there need to be a time contraint on when donations can receive a receipt?
            #or they can only be used once?

            price_ticker = ""
            ticket_valid = 1
            expected = 0
            wish_id = null_if_not_exists(vals,b"uid")
            #enforce ticker symbols
            ticker =  null_if_not_exists(vals,b"coins")
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
    con = sqlite3.connect('clicks.db')
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
def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))


def db_receipts_add(data):
    con = sqlite3.connect('receipts.db')
    cur = con.cursor()
    sql = ''' INSERT INTO donations (email,amount,fname,donation_address,zipcode,address,date_time,refund_address,crypto_ticker,wish_id,comment,comment_name,amount_expected,consent,quantity,type)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    cur.execute(sql, (data["email"],data["amount"],data["fname"],data["donation_address"],data["zipcode"],data["address"],data["date_time"],data["refund_address"],data["crypto_ticker"],data["wish_id"],data["comment"],data["comment_name"],data["amount_expected"],data["consent"],data["quantity"],data["type"]))
    con.commit()

def send_email(db_email,db_amount,db_fname,db_crypto_addr,db_zip,db_address,db_date_time,db_refund_addr,db_ticker,db_wish_id):
    gmail_user = 'xmrdonation@gmail.com'
    gmail_password = 'zxzicneeejwnptvt'

    sent_from = gmail_user
    to = db_email
    subject = f'MAGIC Donation - {db_wish_id}'
    body = f"""Amount: {db_amount}
    Full name: {db_fname}
    Zipcode: {db_zip}
    Street Address: {db_address}
    Crypto Address: {db_crypto_addr}
    Date/Time: {db_date_time}
    Refund Address: {db_refund_addr}
    Crypto Ticker: {db_ticker}
    """
    message = f'Subject: {subject}\n\n{body}'

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message)
        server.close()

        print("Email sent!")
    except:
        print('Something went wrong...')

def ticket_send_email(db_fname,db_email,db_ticker,db_date_time,db_amount,db_amount_expected,db_consent,db_crypto_addr,db_quantity,db_type,success):
    gmail_user = 'xmrdonation@gmail.com'
    gmail_password = 'zxzicneeejwnptvt'
    sent_from = gmail_user
    to = db_email
    if db_type == "ticket":
        db_type = "Standard"
    else:
        db_type = "VIP"
    print(f"sending email to {to}")
    if success == 1:
        subject = f'TicketEroKon tickets Payment Success'
        body = f"""Amount: {db_amount}
        Name: {db_fname}
        Payment Address: {db_crypto_addr}
        Date/Time: {db_date_time}
        Coin type: {db_ticker}
        Expected: {db_amount_expected}
        Paid: {db_amount}
        Ticket quantity: {db_quantity}
        Ticket type: {db_type}
        Consent (1=yes 0=no): {db_consent}

        Thanks for sending the correct amount. You are an angel and deserve both a cookie and a ticket x
        """
    
    else:
        remainder = (db_amount_expected - db_amount)
        subject = f'TicketEroKon tickets Payment Error'
        body = f"""Amount: {db_amount}
        Name: {db_fname}
        Payment Address: {db_crypto_addr}
        Date/Time: {db_date_time}
        Coin type: {db_ticker}
        Expected: {db_amount_expected}
        Paid: {db_amount}
        Ticket quantity: {db_quantity}
        Ticket type: {db_type}
        Consent (1=yes 0=no): {db_consent}

        You didnt send the correct amount. please send another {remainder} to the Payment address x
        """
    message = f'Subject: {subject}\n\n{body}'
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, message)
        server.close()

        print("Email sent!")
    except:
        print('Something went wrong...')

class FiatDonate(BaseModel):
    fname: str
    lname: str
    street: str
    email: str
    id: str
    usd: int
    zip: str
@app.post("/flask/fiat_donate")
def square_checkout(fiatDonate: FiatDonate):
    global LOCATION_ID
    print("Geklo")
    item_dict = fiatDonate.dict()
    #pprint.pprint(item_dict)
    '''
    send_this = {
    "fname": data[0].value,
    "lname": data[1].value,
    "street": data[2].value,
    "zip": data[3].value,
    "email": data[4].value,
    "id": id,
    "usd": usd
    }
    '''
    wish_id = item_dict["id"]
    usd_amount = item_dict["usd"]
    email = item_dict["email"]
    fname = item_dict["fname"]
    lname = item_dict["lname"]
    _zip = item_dict["zip"]
    street = item_dict["street"]
    cc = "TBD"
    order_id = "TBD"
    comment_name="Anonymous"
    comment="Test comment"
    ref_id = str(uuid.uuid4())[0:27] + "@" + wish_id
    con = sqlite3.connect('card_orders.db')
    cur = con.cursor()
    create_orders_table = """ CREATE TABLE IF NOT EXISTS orders (
                                usd integer,
                                ref_id text PRIMARY KEY,
                                email text,
                                fname text,
                                lname text,
                                zip text,
                                street text,
                                cc text,
                                order_id text,
                                date_time text,
                                comment text,
                                comment_name text,
                                amount_expected default 0 not null
                            ); """

    cur.execute(create_orders_table)
    con.commit()


    result = client.checkout.create_checkout(
    location_id = LOCATION_ID,
    body = {
    "idempotency_key": str(uuid.uuid4()),
    "order": {
      "order": {
                    "location_id": LOCATION_ID,
                    "reference_id": ref_id,
                    "customer_id": str(uuid.uuid4()),
                    "line_items": [
                                      {
                                        "uid": str(uuid.uuid4()),
                                        "name": "MAGIC Donation",
                                        "quantity": "1",
                                        "base_price_money": {
                                          "amount": int(usd_amount),
                                          "currency": "GBP"
                                        }
                                      }
                                ],
                    "state": "OPEN"
            },
      "idempotency_key": str(uuid.uuid4())
    },
    "pre_populate_buyer_email": email,
    #"redirect_url" : 'https://getwishlisted.xyz/flask/checkout',
    "merchant_support_email" : "support@magicgrants.org"
    });

    if result.is_success():
        #pprint.pprint(result.body)
        body = result.body
        sql = ''' INSERT INTO orders (usd,ref_id,email,fname,lname,zip,street,cc,order_id,date_time,comment,comment_name)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
        print(f"[DEBUG]: inserting ref_id as: {ref_id}")
        cur.execute(sql, (0,ref_id,email,fname,lname,_zip,street,cc,order_id,str(datetime.now()),comment,comment_name))
        con.commit()
        return body["checkout"]["checkout_page_url"]
    elif result.is_error():
        print(result.errors)
    return '', 200
