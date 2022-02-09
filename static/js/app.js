let modified = "0"



function getWishlist() {
    let ran_int = Math.floor(Math.random() * 100000)
    let url_get = "/static/data/wishlist-data.json?uid=" + ran_int;
    //let url_get = '../data/wishlist-data.json'
    let something = {}
    try {
            $.ajax({
            async: false,
            type: 'GET',
            url: url_get,
            success: function(data) {
                //something = data
                //wishlist = debugWishlist()
                wishlist = data
                modified_live = wishlist["metadata"]["modified"]
                //alert(modified_live)
                //static html is now all there
                //dont need to redraw everything.
                //only whats been updated
                //if static html not updated - it could error for 5 minutes..
                //'checked' status 
                if (modified != modified_live){
                    modified = modified_live
                    let html = '';
                    wishlist["wishlist"].forEach(wish => {
                        let percent_info = getTotal(wish)
                        let sortme = percent_info["values"]
                        console.log(sortme)
                        let total = percent_info["total_usd"]
                        
                        sortme = getSortedKeys(sortme)
                        console.log(sortme)

                        //console.log(sorted)

                        //total["usd"] = 
                        //total["btc"] = %
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
                          "bitcoin": "#f7931a"
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

                        end = `${prc2}%`
                        let htmlSegment =`  
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
                                                 ${one}, ${two}, ${three}, transparent ${end});
                                            }
                                            </style>

                                            <div class ="wish">
                                            <span class="wish_title"><h3>${wish.title}</h3></span></br>
                                            <div class="progress_${wish["id"]}"></div>
                                                
                                                <p class="fundgoal">Raised $${total} of $${wish.goal_usd} Contributors: ${wish.contributors}</p>
                                                <p class="description">${wish.description}</p>

                                                
                                                <br/>
<div class="tabs">
  <input type="checkbox" name="tabs" id="tabone_${wish["id"]}">
  <label class="cointab" for="tabone_${wish["id"]}"><img class="ticker" src="/static/images/xmr.png" alt="XMR"></label>
  <div class="tab">
  <p class="xmr_address" id="${wish.id}">${wish.xmr_address}</br></p>
  <p>[<a href="${wish.qr_img_url_xmr}" data-lightbox="${wish.id}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">${xmr_history}</span></span></p>
  </div>
  
  <input type="checkbox" name="tabs" id="tabtwo_${wish["id"]}">
  <label class="cointab" for="tabtwo_${wish["id"]}"><img class="ticker" src="/static/images/bch.png" alt="BCH"></label>
  <div class="tab">
  <p class="bch_address" id="${wish.id}">${wish.bch_address}</br></p>
  <p>[<a href="${wish.qr_img_url_bch}" data-lightbox="${wish.id}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">${bch_history}</span></span></p>
  </div>
  
  <input type="checkbox" name="tabs" id="tabthree_${wish["id"]}">
  <label class="cointab" for="tabthree_${wish["id"]}"><img class="ticker" src="/static/images/btc.png" alt="BTC"></label>
  <div class="tab">
  <p class="btc_address" id="${wish.id}">${wish.btc_address}</br></p> 
  <p>[<a href="${wish.qr_img_url_btc}" data-lightbox="${wish.id}" data-title="Thank you 😘">QR</a>] <span class="tooltip">[History]<span class="tooltiptext">${btc_history}</span></span>
  </div>
</div>



                                        </div> <hr>`;
                        html += htmlSegment;
                    });
                    let container = document.querySelector('.wishlist');
                    container.innerHTML = html;
    }

            }
            });
    } catch (error) {
        return null;
    }
}
//https://stackoverflow.com/questions/5199901/how-to-sort-an-associative-array-by-its-values-in-javascript/11811767
function getSortedKeys(obj) {
    var keys = Object.keys(obj);
    return keys.sort(function(a,b){return obj[a] - obj[b]});
}

function getPrice(symbol){
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
        "bitcoin-cash": "bch_total"
    }
    let percentages = {
      "values": {
        "monero": 0,
        "bitcoin-cash": 0,
        "bitcoin": 0
      },
      "total_usd": 0
    }

    let total_usd = 0
    let total_percent = 0
    for (var symbol in tickers){
        //array_prices = global
        usd = array_prices[symbol]
        per_coin = (usd * wish[tickers[symbol]])
        percent = (per_coin / wish["goal_usd"]) * 100
        total_percent += percent
        percentages["values"][symbol] = percent
        total_usd += per_coin
     }
     percentages["total_usd"] = total_usd.toFixed(2)
     if (total_percent >= 100){
      //set new values
      percentages["values"].forEach(x => {
        percentages["values"][x] = (percentages["values"][x] / total_percent) * 100
      });

     }
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

function doit(){
  getPrice()
  getWishlist()
}



//on page load - render the wishlist. set a 'time updated variable from the json' then loop compare
//infinite loop
var array_prices = {"bitcoin-cash": 0, "monero": 0, "bitcoin": 0};
function main(){
    doit()
  setInterval(doit,5000)
}
$(main)

