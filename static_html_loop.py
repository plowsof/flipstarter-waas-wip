import configparser
import shutil
import requests 
import random 
from filelock import FileLock
import os
import json
import pprint
#todo handle when goal is overfunded

prices = {}
prices["monero"] = 0
prices["bitcoin-cash"] = 0
prices["bitcoin"] = 0

def main(config):
    www_root = config["wishlist"]["www_root"]
    funding_page = config["wishlist"]["page_name"]
    APPLICATION_ID = config["square"]["APPLICATION_ID"]
    LOCATION_ID = config["square"]["LOCATION_ID"]
    ACCESS_TOKEN = config["square"]["ACCESS_TOKEN"]
 
    #these can probably be hardcoded
    client = Client(
    access_token=ACCESS_TOKEN,
    environment=config.get("square", "environment"),
    )

    location = client.locations.retrieve_location(location_id=LOCATION_ID).body["location"]
    ACCOUNT_CURRENCY = location["currency"]
    ACCOUNT_COUNTRY = location["country"]

    #funding_template = f'template_{funding_page}'
    funding_template = os.path.join(".","html","template_page.html")
    funding_file = os.path.join(www_root,funding_page)
    json_file = os.path.join(www_root,"data","wishlist-data.json")
    if not os.path.isfile(funding_template):
        shutil.copy(funding_file,os.path.join('.',funding_template))
    #get the json 
    with open(json_file,'r') as f:
        wishlist = json.load(f)
    html = ""
    set_global_prices()
    for wish in wishlist["wishlist"]:
        our_data = get_total(wish)
        total = round(our_data["total_usd"],2)
        sortme = our_data["values"]

        sortme = dict(sorted(sortme.items(), key=lambda item: item[1]))
        #pprint.pprint(sortme)
        xmr_history = get_history(wish["xmr_history"])
        bch_history = get_history(wish["bch_history"])
        btc_history = get_history(wish["btc_history"])
        wish["percent"] = (total / float(wish["goal_usd"])) * 100
        colours = {
          "monero": "#f26822",
          "bitcoin-cash": "#0ac18e",
          "bitcoin": "#f7931a"
        }
        sort = list(sortme.keys())
        one = colours[sort[0]]
        prc0 = sortme[sort[0]]
        one += f" {prc0}%"


        two = colours[sort[1]]
        prc1 = sortme[sort[1]]
        prc1 += prc0
        two += f" {prc0}% {prc1}%"

        three = colours[sort[2]]
        prc2 = sortme[sort[2]]
        prc2 += prc1
        three += f" {prc1}% {prc2}%"
        end = f"{prc2}%"

        htmlSegment =f"""  
            <style>
             .progress_{wish['id']} {{
             border-radius: 25px;
             height:10px;
             width:100%;
             border:2px solid #000;
             text-align:center;
             color:#fff;
             font-size:20px;
             background: linear-gradient(to right,
                 {one}, {two}, {three}, transparent {end});
            }}
            </style>
            <div class ="wish">
            <span class="wish_title"><h3>{wish['title']}</h3></span></br>
            <p class="description">{wish['description']}</p>
            <div class="progress_{wish['id']}"></div>
                
                <p class="fundgoal">Raised ${total} of ${wish['goal_usd']} Contributors: {wish['contributors']}</p>
                
                <br/>
                <div class="tabs">
                  <input type="checkbox" name="tabs" id="tabone_{wish['id']}">
                  <label class="cointab" for="tabone_{wish["id"]}"><img class="ticker" src="./logos/monero-xmr-logo.png" alt="XMR"></label>
                  <div class="tab">
                  <p class="xmr_address" id="{wish['id']}">{wish['xmr_address']}</br></p>
                  <p>[<a href="{wish['qr_img_url_xmr']}" data-lightbox="{wish['id']}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{xmr_history}</span></span></p>
                  </div>
                  
                  <input type="checkbox" name="tabs" id="tabtwo_{wish['id']}">
                  <label class="cointab" for="tabtwo_{wish["id"]}"><img class="ticker" src="./logos/bitcoin-cash-bch-logo.png" alt="BCH"></label>
                  <div class="tab">
                  <p class="bch_address" id="{wish['id']}">{wish['bch_address']}</br></p>
                  <p>[<a href="{wish['qr_img_url_bch']}" data-lightbox="{wish['id']}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{bch_history}</span></span></p>
                  </div>
                  
                  <input type="checkbox" name="tabs" id="tabthree_{wish['id']}">
                  <label class="cointab" for="tabthree_{wish["id"]}"><img class="ticker" src="./logos/BTC_Logo.png" alt="BTC"></label>
                  <div class="tab">
                  <p class="btc_address" id="{wish['id']}">{wish['btc_address']}</br></p> 
                  <p>[<a href="{wish['qr_img_url_btc']}" data-lightbox="{wish['id']}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{btc_history}</span></span>
                  </div>
                </div>
        </div> <hr>"""
        html += htmlSegment
    replacement = ""
    with open(funding_template, 'r') as f:
        for line in f:
            if "{@_WISHLIST_@}" in line:
                line = line.replace("{@_WISHLIST_@}", html)
            elif "{@_APPLICATION_ID_@}" in line:
                line = line.replace("{@_APPLICATION_ID_@}", APPLICATION_ID)
            elif "{@_LOCATION_ID_@}" in line:
                line = line.replace("{@_LOCATION_ID_@}", LOCATION_ID)
            elif "{@_ACCOUNT_CURRENCY_@}" in line:
                line = line.replace("{@_ACCOUNT_CURRENCY_@}", ACCOUNT_CURRENCY)
            elif "{@_ACCOUNT_COUNTRY_@}" in line:
                line = line.replace("{@_ACCOUNT_COUNTRY_@}", ACCOUNT_COUNTRY)
            replacement += line
    lock = funding_template + ".lock"
    with FileLock(lock):
        with open(funding_file,'w') as f:
            f.write(replacement)

def get_history(data):
    history = ""
    if not len(data):
        return "No history😥"
    recent = len(data) - 1
    for i in range(len(data)):
        history += ("+" + str(round(data[recent]["amount"],5)) + "<br>")
        recent -= 1
        if i == 4:
            i = len(data)
    return history

def set_global_prices():
    global prices
    ran_int = random.randint(1, 10000)
    for x in prices:
        url_get = f"https://api.coingecko.com/api/v3/simple/price?ids={x}&vs_currencies=usd&uid=" + str(ran_int)
        resp = requests.get(url=url_get)
        data = resp.json()
        prices[x] = data[x]["usd"]
    pprint.pprint(prices)

def get_total(wish):
    prices
    ticker_var = {
        "monero": "xmr_total",
        "bitcoin": "btc_total",
        "bitcoin-cash": "bch_total"
    }

    returnme = {}
    returnme["values"] = {
    "monero": 0,
    "bitcoin-cash": 0,
    "bitcoin": 0
    }

    total_usd = 0
    total_percent = 0
    for x in ticker_var:
        coin = ticker_var[x]
        usd = prices[x]
        this_coin = usd * wish[coin]
        percent = (float(this_coin) / float(wish["goal_usd"])) * 100
        total_percent += percent
        print(f"this_coin = {this_coin} \n wish goal = {wish['goal_usd']}\n percent = {percent}")
        returnme["values"][x] = percent
        total_usd += (this_coin)

    if total_percent >= 100:
        #fully funded 
        for x in returnme["values"]:
            returnme["values"][x] = (returnme["values"][x] / total_percent) * 100

    returnme["total_usd"] = round(total_usd,2)
    return returnme

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    main(config)
