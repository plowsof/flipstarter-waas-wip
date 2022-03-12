let window.num_wishes = 0

function async_getWishlist() 
{
  let ran_int = Math.floor(Math.random() * 100000)
  let url_get = "/donate/static/data/wishlist-data.json?uid=" + ran_int;
  //let url_get = '../data/wishlist-data.json'
  let something = {}
  $.ajax({
    type: 'GET',
    url: url_get,
    success: function(data){
      if ( data.wishlist.length == window.num_wishes ){

      }
      else{
        //delete entire {@wishlist html
        //redraw page
        $(".wishlist").html("")
        updateWishlist(data)
      }
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
      $("span.progress#" + wish.id).text("FUNDED")
      $(".main_buttons#" + wish.id).hide()
      //hide buttons
    }else{
      $("span.progress#" + wish.id).text("")
      //show buttons
      $(".main_buttons#" + wish.id).show()
    }
    //if wish has a status e.g. WIP /RELEASED set here

    //change progress bar style
    $('.progress_' + wish.id).css({
    background: `linear-gradient(to right, ${one}, ${two}, ${three}, ${four}, transparent ${end})`
    });
    //change raised total
    $(".raised#" + wish.id).text(total)
    $(".goal#" + wish.id).text(wish.goal_usd)
  }
}

function init_wish(one,two,three,four,end,total,wish)
{
  if(total >= wish.goal_usd)
  {
    wish.title += " FUNDED"
  }
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
    <span class="wish_title" id="${wish.id}"><h3>${wish.title} </h3></span></span class="progress" id="${wish.id}"></span><span class="status" id="${wish.id}"></span></br>
    <div class="progress_${wish["id"]}"></div></br>
    <span class="fundgoal_${wish.id}">Raised: $<span class="raised" id="${wish.id}">${total}</span> of $<span class="goal" id="${wish.goal_usd}">${wish.goal_usd}</span></span><span class="contributors" id="${wish.id}">Contributors: ${wish.contributors}</span>
    <p class="description">${wish.description}</p>
    <div class="main_buttons" id="${wish.id}">
      <button id="button_${wish["id"]}" type="button" onclick="cryptoClick('${wish.id}')">Donate Crypto</button>
      <button id="${wish["id"]}" type="button" onclick="fiatClick('${wish.id}')">Donate with card</button>
      <div class="crypto_donate" id="crypto_donate_${wish["id"]}"></div>
      <div class="card_donate" id="card_donate_${wish["id"]}"></div>
      <div class="card_donate_${wish["id"]}"></div>
    </div>
  </div> <hr>`
  return htmlSegment
}
