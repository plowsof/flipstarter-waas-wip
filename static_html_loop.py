import configparser
from filelock import FileLock
import os
import json
import pprint
from math import ceil
from main import db_get_prices
#todo handle when goal is overfunded

prices = {}
prices["monero"] = 0
prices["bitcoin-cash"] = 0
prices["bitcoin"] = 0

comments_per_page = 8

def main(config):
    global comments_per_page
    www_root = config["wishlist"]["www_root"]
    funding_page = config["wishlist"]["page_name"]
 
    #funding_template = f'template_{funding_page}'
    funding_template = "template_index.html"
    funding_file = funding_page
    json_file = os.path.join("static","data","wishlist-data.json")
    #get the json 
    with open(json_file,'r') as f:
        wishlist = json.load(f)
    html = ""
    comments = ""
    set_global_prices()
    i = len(wishlist["wishlist"])
    for x in range(len(wishlist["wishlist"])):
        i-=1
        wish = wishlist["wishlist"][i]
        our_data = get_total(wish)
        total = round(our_data["total_usd"],2)
        sortme = our_data["values"]

        sortme = dict(sorted(sortme.items(), key=lambda item: item[1]))
        #pprint.pprint(sortme)
        wish["percent"] = (total / float(wish["goal_usd"])) * 100
        colours = {
          "monero": "#f26822",
          "bitcoin-cash": "#0ac18e",
          "bitcoin": "#f7931a",
          "usd": "green"
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
        four = colours[sort[3]]
        prc3 = sortme[sort[3]]
        prc3 += prc2
        four += f" {prc2}% {prc3}%"
        end = f"{prc3}%"
        htmlSegment = wish_html(one,two,three,four,end,total,wish)
        html += htmlSegment
    replacement = ""
    #pprint.pprint(wishlist["wishlist"])
    htmlComments = comments_html(wishlist["comments"]["comments"])
    count = len(wishlist["comments"]["comments"])
    pages = ceil( count / comments_per_page)
    print(f"the pages = {pages} count = {count}")
    with open(funding_template, 'r') as f:
        for line in f:
            if "{@_WISHLIST_@}" in line:
                line = line.replace("{@_WISHLIST_@}", html)
            elif "{@_COMMENTS_@}" in line:
                line = line.replace("{@_COMMENTS_@}", htmlComments)
            elif "{@_PAGES_@}" in line:
                line = line.replace("{@_PAGES_@}", str(pages))
            replacement += line
    lock = funding_template + ".lock"
    with FileLock(lock):
        with open(funding_file,'w') as f:
            f.write(replacement)
'''
{
    "comment": "What do you think about the &#x27;Accepted-here&#x27; logos in the footer of this page?",
    "comment_name": "HelloWorld",
    "date_time": 1643551019,
    "ticker": "xmr",
    "amount": 0.006516356054,
    "id": "VPS - 3 months"
},
'''
def comments_html(comments):
    global prices
    html_comments = ""
    #comments are actually history
    for i in range(len(comments)):
        #set usd value for each
        if comments[i]["ticker"] == "xmr":
            ticker = "monero"
        elif comments[i]["ticker"] == "bch":
            ticker = "bitcoin-cash"
        elif comments[i]["ticker"] == "btc":
            ticker = "bitcoin"
        comments[i]["usd_value"] = (float(comments[i]["amount"]) * float(prices[ticker]))
    #sort comments from high -> low
    pprint.pprint(comments)
    comments = sorted(comments, key=lambda k:k["usd_value"],reverse=True)
    for i in range(len(comments)):
        commentSegment = ""
        name = comments[i]["comment_name"]
        if name == "":
            name = "Anonymous"
        amount = comments[i]["amount"]
        coin_image = f'<img id="crypto_ticker" src="/flask/static/images/{comments[i]["ticker"]}.png" alt="{comments[i]["ticker"]}" height="20px" width="20px">'
        comment = comments[i]["comment"]
        wish_title = comments[i]["id"]
        commentSegment += f""" 
        <div class="comment">
        <span class="c_name">{name}</span>
        <span class="c_amount">+{round(float(amount),4)} {coin_image}</span></br>
        """
        if comment != "":
            commentSegment += f"""<span class="c_comment">"{comment}"</span></br>"""
        commentSegment+=f"""
        <span class="c_for">{wish_title}</span>
        </div>"""
        html_comments += commentSegment
        

    return html_comments

def wish_html(one,two,three,four,end,total,wish):
    funded = ""
    if total >= wish["goal_usd"]:
        funded = "FUNDED "
    wish_html = f"""  
                  <style>
                    .progress_{wish["id"]} {{
                    border-radius: 25px;
                    height:10px;
                    width:100%;
                    border:2px solid #000;
                    text-align:center;
                    color:#fff;
                    font-size:20px;
                    background: linear-gradient(to right,
                        {one}, {two}, {three}, {four}, transparent {end});
                    }}
                    .crypto_donate_{wish["id"]}{{
                        display:none;
                    }}
                    input[type=checkbox].checkbox_{wish["id"]} {{
                        display: none;
                    }}
                    input[type=checkbox].checkbox_{wish["id"]}:checked~.crypto_donate_{wish["id"]} {{
                        display: block;
                    }}

                  </style>
                  <div class="wish" id="{wish["id"]}">
                    <span class="wish_title" id="{wish["id"]}"><h3>{wish["title"]} </span><span class="prog_{wish["id"]}"></span><span class="status_{wish["id"]}">{funded}{wish["status"]}</span></h3></br>
                    <div class="progress_{wish["id"]}"></div></br>
                    <span class="fundgoal_{wish["id"]}">Raised: $<span class="raised_{wish["id"]}">{total}</span> of $<span class="goal_{wish["id"]}">{wish["goal_usd"]}</span></span><span class="contributors" id="{wish["id"]}"> Contributors: {wish["contributors"]}</span>
                    <p class="description">{wish["description"]}</p>
                    """
    if funded == "": #draw a donate button
        img_xmr = f'<img id="crypto_ticker" src="/flask/static/images/xmr.png" alt="xmr" height="20px" width="20px">'
        img_bch = f'<img id="crypto_ticker" src="/flask/static/images/bch.png" alt="bch" height="20px" width="20px">'
        img_btc = f'<img id="crypto_ticker" src="/flask/static/images/btc.png" alt="btc" height="20px" width="20px">'
        wish_html+= f"""
                          <label for="reveal-donate" class="btn">Donate</label>
                          <input type="checkbox" class="checkbox_{wish["id"]}" id="reveal-donate" role="button">
                          <div class="crypto_donate_{wish["id"]}" id="crypto_donate_{wish["id"]}">
                            <p>{img_xmr}{wish["xmr_address"]}</p>
                            <p>{img_bch}{wish["bch_address"]}</p>
                            <p>{img_btc}{wish["btc_address"]}</p>
                          </div>
                    """
    wish_html += """</div> <hr>"""
    return wish_html


def set_global_prices():
    global prices
    data = db_get_prices()
    for ticker in prices:
        prices[ticker] = data[ticker]

def get_total(wish):
    prices
    ticker_var = {
        "monero": "xmr_total",
        "bitcoin": "btc_total",
        "bitcoin-cash": "bch_total",
        "usd": "usd_total"
    }

    returnme = {}
    returnme["values"] = {
    "monero": 0,
    "bitcoin-cash": 0,
    "bitcoin": 0,
    "usd": 0
    }

    total_usd = 0
    total_percent = 0
    for x in ticker_var:
        if x != "usd":
            coin = ticker_var[x]
            usd = prices[x]
            this_coin = usd * wish[coin]
            percent = (float(this_coin) / float(wish["goal_usd"])) * 100
            total_percent += percent
            print(f"this_coin = {this_coin} \n wish goal = {wish['goal_usd']}\n percent = {percent}")
            returnme["values"][x] = percent
            total_usd += (this_coin)
        else:
            total_usd += wish["usd_total"]
            usd_percent = (wish["usd_total"] / wish["goal_usd"]) * 100
            returnme["values"]["usd"] = usd_percent 
            total_percent += usd_percent

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
#need to take into account the usd value (for recurring payments e.g. vps)
