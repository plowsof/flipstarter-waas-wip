let modified = 0
let num_wishes = 0
let comments_modified = 0
let comment_list = []
let comment_page = 0
let global_wishlist = {}
global_wishlist.wishlist = []

window.total = {}
function drawCryptoDonate(id){

    wishlist = window.wishlist
    wishlist["wishlist"].forEach(_wish => {
        if (_wish.id == id){
            wish = _wish
            return;
        }
    });

    max = Math.ceil(total[`${id}`])
    let donate_crypto = `
    <div class="donate_crypto_${wish["id"]}">
  <form name="donate" id="${wish["id"]}" action="/donate/crypto_donate" method="POST">
  <input type="range" step="0.01" min="0" max="${max}" value="0" class="slider" id="myRange">
  <p>$Amount: <span id="demo">0</p>
  <label for="coins_select">Crypto:</label>
  <select class="coins" name="coins" id="coin_select"> 
    <option id="xmr_${wish["id"]}" value="xmr" rfund="Monero"><img src="/donate/static/images/xmr.png">Monero</option>
    <option id="bch_${wish["id"]}" value="bch" rfund="BitcoinCash"><img src="/donate/static/images/bch.png">BitcoinCash</option>
    <option id="btc_${wish["id"]}" value="btc" rfund="Bitcoin"><img src="/donate/static/images/btc.png">Bitcoin</option>
    <option id="wow_${wish["id"]}" value="wow" rfund="WOWnero"><img src="/donate/static/images/wow.png">WOWnero</option>
  </select></br>
  <input type="radio" id="anon" name="choice" value="anon" checked="checked">
  <label for="anon">Anonymous</label></br>
  <input type="radio" id="tax" name="choice" value="tax">
  <label for="tax">Leave a comment</label></br>
  <button type="button" id="button_qr" onclick="anonUri()">Make Payment QR</button>
  <div class="kyc">
      <label for="display_name">Display name:</label>
      <input placeholder="Anonymous" type="text" id="comment_name" name="comment_name" maxlength="12"></br>
      <textarea id="comment_area" name="comment" rows="4" cols="50" placeholder="Type a message here..." maxlength="140"></textarea>
    <button class="crypto_button" type="submit" id="${wish["id"]}">Get payment address</button>
  </div>
  <div class="anon_address_bch" id="bch_${wish["id"]}">bitcoincash:${wish.bch_address}</div>
  <div class="anon_address_btc" id="btc_${wish["id"]}">bitcoin:${wish.btc_address}</div>
  <div class="anon_address_xmr" id="xmr_${wish["id"]}">monero:${wish.xmr_address}</div>
  <div class="anon_address_wow" id="wow_${wish["id"]}">wownero:${wish.wow_address}</div>
  
</form>
</div>
  <div class="spinner"><img src="/donate/static/images/spinner.gif"></div>
  <div class="donate_qrcode">
    <div id="donate_qrcode"></div>
    <div id="pay_uri"> </div>
  </div>
  `
  return donate_crypto
}

//https://stackoverflow.com/questions/5199901/how-to-sort-an-associative-array-by-its-values-in-javascript/11811767
function getSortedKeys(obj) {
    var keys = Object.keys(obj);
    return keys.sort(function(a,b){return obj[a] - obj[b]});
}

function cryptoClick(id){
    //hide all donate crypto
    $(".crypto_donate").html("")
    $(".card_donate").html("")
    string = drawCryptoDonate(id)
    //console.log(string)
    setHooks(id,string)
    form_validate()
}


async function getPrice(){
  let url_get = `/donate/api/price`
  let price_info
  try {
          price_info = await $.ajax({
          dataType: "json",
          type: 'GET',
          url: url_get
      });
  }catch (error){
      console.log(error)
      return null;
  }
  Object.keys(array_prices).forEach(function(symbol) {
    if (price_info[symbol] == "i") {
      return null;
    }
    array_prices[symbol] = price_info[symbol]
  });
  //don't redraw the list with any price == 0
  async_getWishlist()
}

function getTotal(wish){
    let tickers = {
        "monero": "xmr_total",
        "bitcoin": "btc_total",
        "bitcoin-cash": "bch_total",
        "usd": "usd_total",
        "wownero": "wow_total"
    }
    let percentages = {
      "values": {
        "monero": 0,
        "bitcoin-cash": 0,
        "bitcoin": 0,
        "usd": 0,
        "wownero": 0
      },
      "total_usd": 0
    }

    let total_usd = 0
    let total_percent = 0
    for (var symbol in tickers){
        if (symbol != "usd"){
          //array_prices = global
          usd = array_prices[symbol]
          per_coin = (usd * wish[tickers[symbol]])
          percent = (per_coin / wish["goal_usd"]) * 100
          total_percent += percent
          percentages["values"][symbol] = percent
          total_usd += per_coin
        } else {
          total_usd += wish["usd_total"]
          usd_percent = (wish["usd_total"] / wish["goal_usd"]) * 100
          percentages["values"]["usd"] = usd_percent 
          total_percent += usd_percent
        }
     }
     percentages["total_usd"] = total_usd.toFixed(2)
     if (total_percent >= 100){
      //set new values
      for (var x in percentages["values"]){
        percentages["values"][x] = (percentages["values"][x] / total_percent) * 100
      };
     } else {
     }
     id = wish["id"]
     
     if (total_usd < 0){
      total_usd = total_usd * -1
      total_usd += wish["goal_usd"]
      console.log(`now total_usd = ${total_usd}`)
     } else {
      total_usd = wish["goal_usd"] - total_usd
     }
     
     total[`${id}`] = total_usd
     return percentages    
}

async function download_wishlist(){
  let ran_int = Math.floor(Math.random() * 100000)
  let url_get = "/donate/static/data/wishlist-data.json?uid=" + ran_int;
  return $.ajax({
    type: 'GET',
    url: url_get,
  })
}

async function async_getWishlist() 
{
  do_download = 1
  do_comment = 1
  if(do_download == 1){
    global_wishlist = await download_wishlist() // set global_wishlist
    if ( global_wishlist.wishlist.length != num_wishes ){
      console.log("delete html")
      $(".wishlist").html("")
      }
    num_wishes = global_wishlist.wishlist.length
  }

  if(do_comment == 1){
    console.log(global_wishlist)
    pagination(global_wishlist.comments.comments)
  }
  updateWishlist(global_wishlist)
}

function updateWishlist(data) 
{
  let something = {}
  wishlist = data
  let total = 0
  percent_info = {}
  for (var i = wishlist["wishlist"].length - 1; i >= 0; i--) 
  {
    //leave this wish alone if it is fully funded
    //the backend / static page will show the frozen values
    wish = wishlist["wishlist"][i]
    if (wish["is_funded"] != undefined && wish["is_funded"] == 1){
      //alert(`funded title:${wish['title']}`)
      percent_info = wish["funded_percents"]
      total = wish["goal_usd"]
    } else {
      //alert(`not funded title:${wish["title"]}`)
      wish["is_funded"] = 0
      percent_info = getTotal(wish)
      total = percent_info["total_usd"]
    }
    let sortme = percent_info["values"]
    
    sortme = getSortedKeys(sortme)
    //xmr_history = get_history(wish.xmr_history)
    //bch_history = get_history(wish.bch_history)
    //btc_history = get_history(wish.btc_history)
    //usd_history = get_history(wish.usd_history)
    wish.percent = total / wish.goal_usd * 100;

    //new progress bar
    //background: linear-gradient(to right, #ff4f00 -1000%, #0ac18e 40%, #f7931a 94%, red)
    colours = {
      "monero": "#f26822",
      "bitcoin-cash": "#0ac18e",
      "bitcoin": "#f7931a",
      "usd": "#85bb65",
      "wownero": "#FF6EC7"
    }
    one = colours[sortme[0]] 
    prc0 = percent_info["values"][sortme[0]]
    one += ` ${prc0}%`


    two = colours[sortme[1]]
    prc1 = percent_info["values"][sortme[1]]
    prc1 += prc0
    two += ` ${prc0}% ${prc1}%`

    three = colours[sortme[2]]
    prc2 = percent_info["values"][sortme[2]]
    prc2 += prc1
    three += ` ${prc1}% ${prc2}%`

    four = colours[sortme[3]]
    prc3 = percent_info["values"][sortme[3]]
    prc3 += prc2
    four += ` ${prc2}% ${prc3}%`

    five = colours[sortme[4]]
    prc4 = percent_info["values"][sortme[4]]
    prc4 += prc3
    five += ` ${prc3}% ${prc4}%`

    end = `${prc4}%`
    wish = wishlist["wishlist"][i] 
    id = wishlist["wishlist"][i]["id"]
    len = $("div#"+id).length
    console.log(`num of divs with id ${id} = ${len}`)
    if ( len == 0 ){
      $(".wishlist").append( init_wish(one,two,three,four,five,end,total,wish) )
    }
    //the wish is on the page
    //is it fully 'FUNDED' or revert title = title
    if (Number(total) >= Number(wish.goal_usd) || wish["is_funded"] == 1){
      console.log(`fully funded ${wish.title}`)
      $(".prog_" + wish.id).text("FUNDED")
      $(`.main_buttons_${wish.id}`).hide()
      //hide buttons
    }else{
      console.log(`not fully funded ${wish.title}`)
      //show buttons
      $(".prog_" + wish.id).text("")
      $(`.main_buttons_${wish.id}`).show()
    }
    //if wish has a status e.g. WIP /RELEASED set here

    //change progress bar style
    $('.progress_' + wish.id).css({
    background: `linear-gradient(to right, ${one}, ${two}, ${three}, ${four}, ${five}, transparent ${end})`
    });
    //change raised total
    total = Number(total).toFixed(2)
    $(".raised_" + wish.id).text(total)
    wish["goal_usd"] = Number(wish["goal_usd"]).toFixed(2)
    $(".goal_" + wish.id).text(wish["goal_usd"])
    //set num contributors
    $("span#" + wish.id + ".contributors").text("Contributors: " + wish.contributors)

  }
}

function init_wish(one,two,three,four,five,end,total,wish)
{
  total = Number(total).toFixed(2);
  wish.goal_usd = wish.goal_usd.toFixed(2);
  let htmlSegment = `
  <style>
    .progress_${wish["id"]} {
    border-radius: 25px;
    height:10px;
    width:100%;
    border:2px solid #000;
    text-align:center;
    color:#fff;
    font-size:20px;
    background: linear-gradient(to right,
       ${one}, ${two}, ${three}, ${four}, ${five}, transparent ${end});
    }
  </style>
  <div class="wish" id="${wish.id}">
    <span class="wish_title" id="${wish.id}"><h3 id="wish_title">${wish.title} </span><span class="prog_${wish.id}" id="progress"></span><span class="status_${wish.id}" id="status">${wish.status}</span></h3>
    <div class="progress_${wish["id"]}" id="progress_bar"></div>
    <span class="fundgoal_${wish.id}" id="raised">Raised: $<span class="raised_${wish.id}">${total}</span> of $<span class="goal_${wish.id}">${wish.goal_usd}</span></span><span class="contributors" id="${wish.id}">Contributors: ${wish.contributors}</span>
    <p class="description">${wish.description}</p>
    <div class="main_buttons_${wish.id}" id="${wish.id}">
      <label class="donate_button" id="button_${wish["id"]}" type="button" onclick="cryptoClick('${wish.id}')">Donate</label>
      <div class="crypto_donate" id="crypto_donate_${wish["id"]}"></div>
    </div>
  </div> <hr>`
  return htmlSegment
}


function doit(){
  getPrice()
  //getWishlist()
  //async_getWishlist()
}

async function pagination(comments){
  commentSegment = ""
  comment_list = []
  per_page = 0
  //var array_prices = {"bitcoin-cash": 0, "monero": 0, "bitcoin": 0};
  for (var i = comments.length - 1; i >= 0; i--) {
    if (comments[i].ticker == "xmr"){
      symbol = "monero"
    } else if (comments[i].ticker == "bch"){
      symbol = "bitcoin-cash"
    } else if (comments[i].ticker == "btc"){
      symbol = "bitcoin"
    } else {
      symbol = "wownero"
    }

    comments[i].usd_value = (comments[i].amount * array_prices[symbol])
  }
  //we have usd_value set. rank them
  comments.sort((a, b) => a.usd_value - b.usd_value)
  
  for (var i = comments.length - 1; i >= 0; i--) {
    let name = comments[i].comment_name 
    if(name == ""){
      name = "Anonymous"
    }
    let amount = comments[i].amount
    let ticker = `<img id="crypto_ticker" src="/donate/static/images/${comments[i].ticker}.png" alt="${comments[i].ticker}" height="20px" width="20px">`
    let comment = comments[i].comment
    let wish_title = comments[i].id
    commentSegment += ` 
    <div class="comment">
    <span class="c_name">${name}</span>
    <span class="c_amount">+${Number(amount).toFixed(4)} ${ticker}</span></br>
    `
    if (comment != ""){
      commentSegment += `<span class="c_comment">"${comment}"</span></br>`
    }
    commentSegment+=
    `
    <span class="c_for">${wish_title}</span>
    </div>`
    if(per_page == 7){
      comment_list.push(commentSegment)
      per_page = 0
      commentSegment = ""
    } else {
      per_page += 1
    }
  };
  if (commentSegment != ""){
    comment_list.push(commentSegment)
  }
  $("span#p_total").html(comment_list.length)
  $("td#history").html(comment_list[comment_page])
}



//on page load - render the wishlist. set a 'time updated variable from the json' then loop compare
//infinite loop
var array_prices = {"bitcoin-cash": "i", "monero": "i", "bitcoin": "i", "wownero": "i"};
function main(){
  $("span#p_left").click(function() {
    console.log(comment_page)
    console.log(`length ${comment_list.length}`)
    if(comment_page != 0){
      comment_page -= 1
      $("td#history").html(comment_list[comment_page])
      $("span#p_num").html(comment_page + 1)
    }
  });
  
  $( "span#p_right" ).click(function() {
    console.log(comment_page)
    console.log(`length ${comment_list.length}`)
    if(comment_page < (comment_list.length - 1)){
      comment_page += 1
      console.log(comment_page)
      console.log(comment_list)
      $("td#history").html(comment_list[comment_page])
      $("span#p_num").html(comment_page + 1)
    }
  });
  modified = 0
  doit()

  //setInterval(doit,(1000*60))
}
$(main)

//update 'raised x of y' and progress bar &