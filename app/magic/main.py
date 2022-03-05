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
from square.client import Client
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
NOTIFICATION_URL = 'https://getwishlisted.xyz/flask/webhook'

# The event notification subscription signature key (sigKey) defined in dev portal for app.
SIG_KEY = b'iMC2A7ZgK1M02FSJWBSe8Q';

# To read your secret credentials
config = configparser.ConfigParser()
config.read("config.ini")

wish_config = configparser.ConfigParser()
wish_config.read("./db/wishlist.ini")

# Retrieve credentials based on is_prod
CONFIG_TYPE = config.get("DEFAULT", "environment").upper()
PAYMENT_FORM_URL = (
    "https://web.squarecdn.com/v1/square.js"
    if CONFIG_TYPE == "PRODUCTION"
    else "https://sandbox.web.squarecdn.com/v1/square.js"
)
APPLICATION_ID = config.get(CONFIG_TYPE, "square_application_id")
LOCATION_ID = config.get(CONFIG_TYPE, "square_location_id")
ACCESS_TOKEN = config.get(CONFIG_TYPE, "square_access_token")

client = Client(
    access_token=ACCESS_TOKEN,
    environment=config.get("DEFAULT", "environment"),
)

location = client.locations.retrieve_location(location_id=LOCATION_ID).body["location"]
ACCOUNT_CURRENCY = location["currency"]
ACCOUNT_COUNTRY = location["country"]

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

@app.post("/flask/checkout")
async def get_body(request: Request,status_code=200):
    print("hello world")

@app.post("/flask/webhook")
async def get_body(request: Request,status_code=200):
    global NOTIFICATION_URL, SIG_KEY, client
    body = await request.body()
    length = int(request.headers['content-length'])
    square_signature = request.headers['x-square-signature']

    #print(length)
    #print(square_signature)

    url_request_bytes = NOTIFICATION_URL.encode('utf-8') + body

    # create hmac signature
    hmac_code = hmac.new(SIG_KEY, msg=None, digestmod='sha1')
    hmac_code.update(url_request_bytes)
    hash = hmac_code.digest()

    # compare to square signature from header
    if base64.b64encode(hash) != square_signature.encode('utf-8'):
        print("sig dont match")
        return ''
    data = json.loads(body.decode('utf-8'))
    #pprint.pprint(data[""]
    #get order id
    #get information (email / wish id) using order id
   
    print("Hello world")
    if (data["data"]["object"]["payment"]["status"]) != "COMPLETED":
        return ''

    order_id = data["data"]["object"]["payment"]["order_id"]
    #refid
    result = client.orders.retrieve_order(
      order_id = order_id
    )
    body = result.body
    #pprint.pprint(body)
    ref_id = body["order"]["reference_id"]
    #amount
    usd = data["data"]["object"]["payment"]["amount_money"]["amount"] / 100
    #confirm we've never seen this order_id before becaus ei noticed duplicate
    #if order id not in db - return - or add it and continue  
    con = sqlite3.connect('./db/card_orders.db')
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
                                date_time text
                            ); """

    cur.execute(create_orders_table)
    cur.execute('SELECT * FROM orders WHERE ref_id = ?',[ref_id])
    rows = cur.fetchall()
    print(f"[DEBUG] row data: {rows[0][8]}\n[DEBUG] != {order_id}")
    if rows[0][8] != order_id:
        print("We got monEY")
        sql = ''' UPDATE orders
          SET order_id = ?,
          usd = ?
          WHERE ref_id = ?'''   
        cur.execute(sql, (order_id,usd,ref_id))
        db_usd = usd 
        db_ref_id = rows[0][1]
        db_email = rows[0][2]
        db_fname = rows[0][3]
        db_lname = rows[0][4]
        db_zip = rows[0][5]
        db_street = rows[0][6]
        db_cc = rows[0][7]
        db_order_id = order_id
        db_date_time = rows[0][8]
        wishlist_usd_notify(db_usd,db_ref_id,db_email,db_fname,db_lname,db_zip,db_street,db_cc,db_order_id,db_date_time)
    con.commit()

def wishlist_usd_notify(db_usd,db_ref_id,db_email,db_fname,db_lname,db_zip,db_street,db_cc,db_order_id,db_date_time):
    global wish_config
    www_root = wish_config["wishlist"]["www_root"]
    wish_id = db_ref_id.split("@")[1]
    data_fname = os.path.join(www_root,"data","wishlist-data.json")
    with open(data_fname, "r") as f:
        data_wishlist = json.load(f)
    found = 0
    found_index = -1
    for i in range(len(data_wishlist["wishlist"])):
        if data_wishlist["wishlist"][i]["id"] == wish_id:
            found = 1
            data_wishlist["wishlist"][i]["usd_total"] += int(db_usd) #in cents i think
            history_tx = {
                "amount":int(db_usd),
                "date_time": db_date_time
            }
            data_wishlist["wishlist"][i]["usd_history"].append(history_tx)
            data_wishlist["wishlist"][i]["contributors"] += 1
            data_wishlist["wishlist"][i]["modified_date"] = db_date_time
            found_index = i
            break
    if found == 1: 
        #save new wishlist with file lock
        lock = data_fname + ".lock"
        with FileLock(lock):
            #print("Lock acquired.")
            with open(data_fname, 'w+') as f:
                json.dump(data_wishlist, f, indent=6)  
    else:
        print("donated to a none existing or archived wish")

    #email alert
    db_wish_id = data_wishlist["wishlist"][int(found_index)]["title"]
    db_crypto_addr = "FIAT"
    db_refund_addr = "FIAT"
    db_ticker = "USD"
    send_email(db_email,db_usd,db_fname,db_crypto_addr,db_zip,db_street,db_date_time,db_refund_addr,db_ticker,db_wish_id)


@app.post("/flask/crypto_donate")
async def handle_crypto_form(request: Request):
    global wish_config, ticket_normal, ticket_vip
    body = await request.body()
    #b'amount=1&coins=xmr&choice=tax&fname=&fname=&street=&zip=&email=&rfund='
    config = configparser.ConfigParser()
    config.read("./db/wishlist.ini")
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
                
        print("loop finished")
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
            if not valid_email(the_email):
                return
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
                    address = address_create_notify(bin_dir,wallet_path,port,addr="",create=1,notify=1)
                    valid_coin = 1
                if vals[b'coins'][0] == b"btc":
                    wallet_path = wish_config["btc"]["wallet_file"]
                    bin_dir = wish_config["btc"]["bin"]
                    port = wish_config["callback"]["port"]
                    address = address_create_notify(bin_dir,wallet_path,port,addr="",create=1,notify=1)
                    valid_coin = 1

                if "not" in address:
                    return
                if valid_coin == 0:
                    return

                con = sqlite3.connect('./db/receipts.db')
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
                                            type text
                                        ); """

                cur.execute(create_receipts_table)
                con.commit()
                cur.execute('SELECT * FROM donations WHERE address = ?',[address])
                rows = len(cur.fetchall())
                pprint.pprint(cur.fetchall())
                #its a new address. continue
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
                crypto_price = getPrice("eur",ticker)
                print(f"crypto price = {crypto_price}")
                ticket_total = ticket_price * ticket_amount
                print(f"ticket total = {ticket_total}")
                expected = round((ticket_total / crypto_price),12)
            else:
                print("error ticket_valid = 0")

            print(f"the donation address is {address}")
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
            "comment": null_if_not_exists(vals,b"comment"),
            "comment_name": null_if_not_exists(vals,b"comment_name"),
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

def getPrice(currency,ticker):
    ran_int = random.randint(1, 10000)
    url_get = f"https://api.coingecko.com/api/v3/simple/price?ids={ticker}&vs_currencies=eur&uid=" + str(ran_int)
    resp = requests.get(url=url_get)
    data = resp.json()
    pprint.pprint(data)
    price = data[ticker][currency]
    return price


def null_if_not_exists(vals,index):
    try:
        if index == b"comment":
            return escape(vals[index][1].decode("utf-8"))
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
                                ip text PRIMARY KEY
                            ); """

    cur.execute(create_clicks_table)
    con.commit()
    cur.execute('SELECT * FROM clicks WHERE ip = ?',[client_ip])
    rows = cur.fetchall()
    if len(rows) == 0:
        #we didnt click today
        #insert into db then return true
        sql = ''' INSERT INTO clicks (ip,clicks)
                  VALUES(?,?) '''
        cur.execute(sql, (client_ip,1))
        con.commit()
        return True

    for row in rows:
        if row[0] > 19:
            return False
        else:
            clicks = row[0]
            clicks += 1
            print(f"clicks={clicks}")
            sql = ''' UPDATE clicks
                      SET clicks = ?
                      WHERE ip = ?'''   
            cur.execute(sql, (clicks,client_ip))
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
    con = sqlite3.connect('./db/receipts.db')
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
    con = sqlite3.connect('./db/card_orders.db')
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
