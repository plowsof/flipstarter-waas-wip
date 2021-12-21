import configparser
import shutil
import requests 
import random 
from filelock import FileLock
import os
import json

def main(config):
    www_root = config["wishlist"]["www_root"]
    funding_page = config["wishlist"]["page_name"]
    #funding_template = f'template_{funding_page}'
    funding_template = "index.html"
    funding_file = os.path.join(www_root,funding_page)
    json_file = os.path.join(www_root,"data","wishlist-data.json")
    if not os.path.isfile(funding_template):
        shutil.copy(funding_file,os.path.join('.',funding_template))
    #get the json 
    with open(json_file,'r') as f:
        wishlist = json.load(f)
    html = ""
    for wish in wishlist["wishlist"]:
        total = get_total(wish)
        xmr_history = get_history(wish["xmr_history"])
        bch_history = get_history(wish["bch_history"])
        btc_history = get_history(wish["btc_history"])
        wish["percent"] = (total / wish["goal_usd"]) * 100
        htmlSegment =f"""  <div class ="wish">
                    <li>
                        <span class="wish_title">{wish["title"]}</span></br>
                        <p class="description">{wish["description"]}</p>
                        <i class="fundgoal">Raised ${total} of ${wish["goal_usd"]} <progress id="file" max="100" value="{wish["percent"]}">{wish["percent"]}%</progress> Contributors: {wish["contributors"]}</i>
                        <label for="file"></label><br/>
                        <img class="ticker" src="./logos/monero-xmr-logo.png" alt="XMR">
                        <p class="xmr_address" id="{wish["id"]}">{wish["xmr_address"]}</br></p>
                        <p>[<a href="{wish["qr_img_url_xmr"]}" data-lightbox="{wish["id"]}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{xmr_history}</span></span></p>
                        <img class="ticker" src="./logos/bitcoin-cash-bch-logo.png" alt="BCH">
                        <p class="bch_address" id="{wish["id"]}">{wish["bch_address"]}</br></p>
                        <p>[<a href="{wish["qr_img_url_bch"]}" data-lightbox="{wish["id"]}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{bch_history}</span></span></p>
                        <img class="ticker" src="./logos/BTC_Logo.png" alt="BTC">
                        <p class="btc_address" id="{wish["id"]}">{wish["btc_address"]}</br></p> 
                        <p>[<a href="{wish["qr_img_url_btc"]}" data-lightbox="{wish["id"]}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">{btc_history}</span></span>
                    </li>
                </div>""";
        html += htmlSegment;
    replacement = ""
    with open(funding_template, 'r') as f:
        for line in f:
            if "{@_WISHLIST_@}" in line:
                line = line.replace("{@_WISHLIST_@}", html)
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

def get_total(wish):
    ticker_var = {
        "monero": "xmr_total",
        "bitcoin": "btc_total",
        "bitcoin-cash": "bch_total"
    }
    total_usd = 0
    for x in ticker_var:
        ran_int = random.randint(1, 10000)
        url_get = f"https://api.coingecko.com/api/v3/simple/price?ids={x}&vs_currencies=usd&uid=" + str(ran_int)
        resp = requests.get(url=url_get)
        data = resp.json()
        coin = ticker_var[x]
        usd = data[x]["usd"]
        total_usd += (usd * wish[coin])
    return round(total_usd,2)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('wishlist.ini')
    main(config)
