import configparser
from filelock import FileLock
import os
import json
import pprint
from math import ceil
import sqlite3

prices = {}
prices["monero"] = 0
prices["bitcoin-cash"] = 0
prices["bitcoin"] = 0

comments_per_page = 8

def main(config):
    global comments_per_page
    www_root = config["wishlist"]["www_root"]
    funding_page = "./static/index.html"
 
    #funding_template = f'template_{funding_page}'
    funding_template = "./static/template_index.html"
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
        total = "%.2f" % (our_data["total_usd"])
        sortme = our_data["values"]
        sortme = dict(sorted(sortme.items(), key=lambda item: item[1]))
        #pprint.pprint(sortme)
        wish["percent"] = (float(total) / float(wish["goal_usd"])) * 100
        colours = {
          "monero": "#f26822",
          "bitcoin-cash": "#0ac18e",
          "bitcoin": "#f7931a",
          "usd": "#85bb65"
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
    intro = config["wishlist"]["intro"]
    #print(f"the pages = {pages} count = {count}")
    with open(funding_template, 'r') as f:
        for line in f:
            if "{@_WISHLIST_@}" in line:
                line = line.replace("{@_WISHLIST_@}", html)
            elif "{@_COMMENTS_@}" in line:
                line = line.replace("{@_COMMENTS_@}", htmlComments)
            elif "{@_PAGES_@}" in line:
                line = line.replace("{@_PAGES_@}", str(pages))
            elif "{@_RSS_@}" in line:
                if config["RSS"]["enable"] == "1":
                    rss_feed = "/donate/static/rss/rss.xml"
                    rss_img =  "/donate/static/images/rss.png"
                    rss_link = f""" <a href='{rss_feed}' width=16" height="16">
                                     <img class="rss_logo" alt='rss' src='{rss_img}'>
                                    </a>"""
                    line=line.replace("{@_RSS_@}",rss_link)
                    #add an rss feed icon
                else:
                    line=line.replace("{@_RSS_@}","")
            elif "{@_INTRO_@}" in line:
                line = line.replace("{@_INTRO_@}",intro)

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
    #pprint.pprint(comments)
    comments = sorted(comments, key=lambda k:k["date_time"],reverse=True)
    comments = sorted(comments, key=lambda k:k["usd_value"],reverse=True)
    for i in range(len(comments)):
        commentSegment = ""
        name = comments[i]["comment_name"]
        if name == "":
            name = "Anonymous"
        amount = comments[i]["amount"]
        coin_image = f'<img id="crypto_ticker" src="/donate/static/images/{comments[i]["ticker"]}.png" alt="{comments[i]["ticker"]}" height="20px" width="20px">'
        comment = comments[i]["comment"]
        wish_title = comments[i]["id"]
        rounded = str(round(float(amount),4))
        trail_0 = "0000"
        if len(rounded.split(".")[1]) != 4:
            rounded += trail_0[0:(4-len(rounded.split(".")[1]))]

        commentSegment += f""" 
        <div class="comment">
        <span class="c_name">{name}</span>
        <span class="c_amount">+{rounded} {coin_image}</span></br>
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
    total = '%.2f' % float(total)
    wish["goal_usd"] = '%.2f' % float(wish["goal_usd"]) 
    if float(total) >= float(wish["goal_usd"]):
        funded = "FUNDED"
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
                    <span class="wish_title" id="{wish["id"]}"><h3 id="wish_title">{wish["title"]} <span class="prog_{wish["id"]}" id="progress">{funded}</span><span class="status_{wish["id"]}" id="status">{wish["status"]}</span></h3>
                    <div class="progress_{wish["id"]}" id="progress_bar"></div>
                    <span class="fundgoal_{wish["id"]}" id="raised">Raised: $<span class="raised_{wish["id"]}">{total}</span> of $<span class="goal_{wish["id"]}">{wish["goal_usd"]}</span></span><span class="contributors" id="{wish["id"]}"> Contributors: {wish["contributors"]}</span>
                    <p class="description">{wish["description"]}</p>
                    """
    if funded == "": #draw a donate button
        img_xmr = f'<img id="crypto_ticker" src="/donate/static/images/xmr.png" alt="xmr" height="20px" width="20px">'
        img_bch = f'<img id="crypto_ticker" src="/donate/static/images/bch.png" alt="bch" height="20px" width="20px">'
        img_btc = f'<img id="crypto_ticker" src="/donate/static/images/btc.png" alt="btc" height="20px" width="20px">'
        wish_html+= f"""
                          <label for="reveal-donate_{wish["id"]}" class="btn">Donate</label>
                          <input type="checkbox" class="checkbox_{wish["id"]}" id="reveal-donate_{wish["id"]}" role="button">
                          <div class="crypto_donate_{wish["id"]}" id="crypto_donate_{wish["id"]}">
                            <p>To leave a comment, javascript must be enabled. Donations should appear within 5 minutes</p>
                            <p>
                                <span class="njs_ticker">{img_xmr} Monero <a href="{wish["qr_img_url_xmr"]}">[QRcode]</a></span></br>
                                <span class="xmr_address">monero:{wish["xmr_address"]}</span>
                            </p>
                            <p>
                                <span class="njs_ticker">{img_bch} Bitcoin Cash <a href="{wish["qr_img_url_bch"]}">[QRcode]</a></span></br>
                                <span class="bch_address">bitcoincash:{wish["bch_address"]}</span>
                            </p>
                            <p>
                                <span class="njs_ticker">{img_btc} Bitcoin <a href="{wish["qr_img_url_btc"]}">[QRcode]</a></span></br>
                                <span class="btc_address">bitcoin:{wish["btc_address"]}</span>
                            </p>
                        </span>
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
            #print(f"this_coin = {this_coin} \n wish goal = {wish['goal_usd']}\n percent = {percent}")
            returnme["values"][x] = percent
            total_usd += (this_coin)
        else:
            total_usd += wish["usd_total"]
            usd_percent = (int(wish["usd_total"]) / int(wish["goal_usd"])) * 100
            returnme["values"]["usd"] = usd_percent 
            total_percent += usd_percent

    if total_percent >= 100:
        #fully funded 
        for x in returnme["values"]:
            returnme["values"][x] = (returnme["values"][x] / total_percent) * 100

    returnme["total_usd"] = round(total_usd,2)
    return returnme

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
    con.close()
    try:
        return_me = {
        "bitcoin-cash": rows[0][3],
        "monero": rows[0][1],
        "bitcoin": rows[0][2]
        }
        return return_me
    except:
        return False

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('./db/wishlist.ini')
    main(config)