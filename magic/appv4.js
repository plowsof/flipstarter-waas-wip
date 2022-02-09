let modified = 0
let num_wishes = 0
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
  <form name="donate" id="${wish["id"]}" action="/flask/crypto_donate" method="POST">
  <input type="range" min="1" max="${max}" value="1" class="slider" id="myRange">
  <p>Amount: <input type="text" id="demo" name="amount" value="1"></p>
  <label for="coins_select">Crypto:</label>
  <select class="coins" name="coins" id="coin_select"> 
    <option id="xmr_${wish["id"]}" value="xmr" rfund="Monero"><img src="/flask/static/images/xmr.png">Monero</option>
    <option id="bch_${wish["id"]}" value="bch" rfund="BitcoinCash"><img src="/flask/static/images/bch.png">BitcoinCash</option>
    <option id="btc_${wish["id"]}" value="btc" rfund="Bitcoin"><img src="/flask/static/images/btc.png">Bitcoin</option>
  </select></br>
 
  <input type="radio" id="anon" name="choice" value="anon" checked="checked">
  <label for="anon">Anonymous</label></br>
  <input type="radio" id="tax" name="choice" value="tax">
  <label for="tax">Tax Receipt</label></br>
  <button type="button" id="button_qr" onclick="anonUri()">Make Payment QR</button>
  <div class="kyc">
    <label for="fname">First name: </label>
    <input type="text" id="fname" name="fname"></br>
    <label for="lname">Last name: </label>
    <input type="text" id="lname" name="lname"></br>
    <label for="street">Street Address: </label>
    <input type="text" id="street" name="street"></br>
    <label for="zip">Zip Code: </label>
    <input type="text" id="zip" name="zip"></br>
    <label for="email">Email: </label>
    <input type="text" id="email" name="email"></br>
    <label id="rfund" for="rfund">Monero Refund Address: </label>
    <input placeholder="Optional" type="text" id="rfund" name="rfund"></br>
    <label for="comment">Message:</label>
    <input type="checkbox" id="input_comment" name="comment"></br>
    
    <div class="message_input">
      <label for="display_name">Display name:</label>
      <input placeholder="Anonymous" type="text" name="comment_name"></br>
      <textarea name="comment" rows="4" cols="50" placeholder="Type a message here..."></textarea>
    </div>
    <button class="crypto_button" type="submit" id="${wish["id"]}">Get payment address</button>
  </div>
  <div class="anon_address_bch" id="bch_${wish["id"]}">${wish.bch_address}</div>
  <div class="anon_address_btc" id="btc_${wish["id"]}">${wish.btc_address}</div>
  <div class="anon_address_xmr" id="xmr_${wish["id"]}">${wish.xmr_address}</div>
  
</form>
</div>
  <div class="spinner"><img src="/flask/static/images/spinner.gif"></div>
  <div class="donate_qrcode">
    <div id="donate_qrcode"></div>
    <div id="pay_uri"> </div>
  </div>
  `
  return donate_crypto
}

function drawCardDonate(id){
  wishlist = window.wishlist
  wishlist["wishlist"].forEach(_wish => {
      if (_wish.id == id){
          wish = _wish
          return;
      }
  });
  max = Math.ceil(total[`${id}`])

  if (max > 25000){
    max = 25000
  }
  let html = 
    `
    <div class="card_donate">
      <input type="range" min="1" max="${max}" value="1" class="slider" id="myRange">
      <form name="card_donate" id="${wish["id"]}" action="/flask/fiat_donate" method="POST">
      <div class="card_kyc">
        <label for="fname">First name: </label>
        <input type="text" id="fname" name="fname"></br>
        <label for="lname">Last name: </label>
        <input type="text" id="lname" name="lname"></br>
        <label for="street">Street Address: </label>
        <input type="text" id="street" name="street"></br>
        <label for="zip">Zip Code: </label>
        <input type="text" id="zip" name="zip"></br>
        <label for="email">Email: </label>
        <input type="text" id="email" name="email"></br>
        <button class="card_button" id="card_button" type="submit">Donate $</button>
      </div>
    </div>`
  return html
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

function fiatClick(id){
  $(".crypto_donate").html("")
  $(".card_donate").html("")
  string = drawCardDonate(id)
  setHooksCard(id,string)
  card_validate()
}

function getPrice(){
    //alert(symbol)
  let ran_int = Math.floor(Math.random() * 100000)
  //alert(array_prices.length)
  Object.keys(array_prices).forEach(function(symbol) {
    let url_get = `https://api.coingecko.com/api/v3/simple/price?ids=${symbol}&vs_currencies=usd&uid=` + ran_int
    try {
         $.ajax({
            async: false,
            type: 'GET',
            url: url_get,
            success: function(data) {
                //callback
                array_prices[symbol] = data[symbol]["usd"]
            }
        });
    }catch (error){
        console.log(error)
        return null;
    }
  });
}


function getTotal(wish){
    let tickers = {
        "monero": "xmr_total",
        "bitcoin": "btc_total",
        "bitcoin-cash": "bch_total",
        "usd": "usd_total"
    }
    let percentages = {
      "values": {
        "monero": 0,
        "bitcoin-cash": 0,
        "bitcoin": 0,
        "usd": 0
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

function get_history(inputs){
    if (inputs.length){
        //we have history
        let i = 0
        let history = ""
        while(i < inputs.length){
            history += ("+" + inputs.at(i).amount.toFixed(5) + "<br>")
            if (i == 4){
                i = inputs.length
            }else{
                i++
            }
        }
        return history
    }else{
        return "No history😥"
    }
}

function async_getWishlist() 
{
  let ran_int = Math.floor(Math.random() * 100000)
  let url_get = "/flask/static/data/wishlist-data.json?uid=" + ran_int;
  //let url_get = '../data/wishlist-data.json'
  let something = {}
  $.ajax({
    type: 'GET',
    url: url_get,
    success: function(data){

      console.log(`is ${data.wishlist.length} == ${num_wishes}`)
      if ( data.wishlist.length != num_wishes ){
        console.log("delete html")
        $(".wishlist").html("")
      }
      num_wishes = data.wishlist.length
      updateWishlist(data)
    }
  })
}


function updateWishlist(data) 
{
  let something = {}
  wishlist = data
  for (var i = wishlist["wishlist"].length - 1; i >= 0; i--) 
  {
    wish = wishlist["wishlist"][i]
    let percent_info = getTotal(wish)
    let sortme = percent_info["values"]
    let total = percent_info["total_usd"]
    sortme = getSortedKeys(sortme)
    xmr_history = get_history(wish.xmr_history)
    bch_history = get_history(wish.bch_history)
    btc_history = get_history(wish.btc_history)
    usd_history = get_history(wish.usd_history)
    wish.percent = total / wish.goal_usd * 100;

    //new progress bar
    //background: linear-gradient(to right, #ff4f00 -1000%, #0ac18e 40%, #f7931a 94%, red)
    colours = {
      "monero": "#f26822",
      "bitcoin-cash": "#0ac18e",
      "bitcoin": "#f7931a",
      "usd": "#85bb65"
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

    end = `${prc3}%`
    wish = wishlist["wishlist"][i] 
    id = wishlist["wishlist"][i]["id"]
    len = $("div#"+id).length
    if ( $("div#"+id).length == 0 ){
      $(".wishlist").append( init_wish(one,two,three,four,end,total,wish) )
    }
    //the wish is on the page
    //is it fully 'FUNDED' or revert title = title
    if (total >= wish.goal_usd){
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
    background: `linear-gradient(to right, ${one}, ${two}, ${three}, ${four}, transparent ${end})`
    });
    //change raised total
    $(".raised_" + wish.id).text(total)
    $(".goal_" + wish.id).text(wish.goal_usd)
  }
}

function init_wish(one,two,three,four,end,total,wish)
{
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
       ${one}, ${two}, ${three}, ${four}, transparent ${end});
    }
  </style>
  <div class="wish" id="${wish.id}">
    <span class="wish_title" id="${wish.id}"><h3>${wish.title} </span><span class="prog_${wish.id}"></span><span class="status_${wish.id}"></span></h3></br>
    <div class="progress_${wish["id"]}"></div></br>
    <span class="fundgoal_${wish.id}">Raised: $<span class="raised_${wish.id}">${total}</span> of $<span class="goal_${wish.id}">${wish.goal_usd}</span></span><span class="contributors" id="${wish.id}">Contributors: ${wish.contributors}</span>
    <p class="description">${wish.description}</p>
    <div class="main_buttons_${wish.id}" id="${wish.id}">
      <button id="button_${wish["id"]}" type="button" onclick="cryptoClick('${wish.id}')">Donate Crypto</button>
      <button id="${wish["id"]}" type="button" onclick="fiatClick('${wish.id}')">Donate with card</button>
      <div class="crypto_donate" id="crypto_donate_${wish["id"]}"></div>
      <div class="card_donate" id="card_donate_${wish["id"]}"></div>
      <div class="card_donate_${wish["id"]}"></div>
    </div>
  </div> <hr>`
  return htmlSegment
}


function doit(){
  getPrice()
  //getWishlist()
  async_getWishlist()
}





//on page load - render the wishlist. set a 'time updated variable from the json' then loop compare
//infinite loop
var array_prices = {"bitcoin-cash": 0, "monero": 0, "bitcoin": 0};
function main(){
  ticket_validate()
  doit()
  setInterval(doit,5000)
}
$(main)

//update 'raised x of y' and progress bar &