//slider.max=1440.5; 

function anonUri(){
  //get price on slider
  $(".spinner").show()
  var usd_value = document.getElementById("myRange").value
  //get coin
  var coin = $(".coins").children(":selected").attr("value")
  //get usd value -> coin amount
  if (coin == "xmr") {
    uri = "monero:"
    str_amount = "tx_amount"
    symbol = "monero"
    //?tx_amount=239
  } else if (coin == "bch"){
    uri = "bitcoincash:"
    str_amount = "amount"
    symbol = "bitcoin-cash"
  } else if (coin == "btc"){
    uri = "bitcoin:"
    str_amount = "amount"
    symbol = "bitcoin"
  } else {
    uri = "wownero:"
    str_amount = "tx_amount"
    symbol = "wownero"
  }
  price = getPriceSingle(symbol)

  total_coins = usd_value / price
  //draw spinner
  
  $("#donate_qrcode").html("")
  //draw qr code
  address = $(".anon_address_" + coin).text()
  //the addresses are displayed with their uris "ticker:" already.
  payment_uri = address + "?" + str_amount + "=" + total_coins.toFixed(12)
  var typeNumber = 0;
  var errorCorrectionLevel = 'L';
  var qr = qrcode(typeNumber, errorCorrectionLevel);
  qr.addData(payment_uri);
  qr.make();
  $('#donate_qrcode').html(qr.createImgTag())
  $('#donate_qrcode').children("img").css('width', "70%")
  $('#donate_qrcode').children("img").css('height', "auto")
  $(".spinner").hide()

  $("#pay_uri").html(`<a class="launch_wallet" href="${payment_uri}">Launch in wallet</a> 1 ${coin} = $${price}`)
}

function getPriceSingle(symbol){
  return array_prices[symbol]
}


function displayAnon() {
  var id = $(".coins").children(":selected").attr("value");
  $("#donate_qrcode").html("");
  $("#pay_uri").html("")
  //only if anonymous is checked display these fixed addresses-
  //alert("display anon")
  if ($('#anon').is(":checked")){
    //alert("Yep its checked")
    $(".anon_address_xmr").hide()
    $(".anon_address_bch").hide()
    $(".anon_address_btc").hide()
    $(".anon_address_wow").hide()
    //alert(id)
    $(".anon_address_" + id).show()
  } else {
      $("#donate_qrcode").html("")
  }
  var val = $(".coins").children(":selected").attr("rfund");
  $("label#rfund").html(val + " Refund Address")
  $("input#rfund").val("")
}

function setHooksCard(id,string){
  $("#card_donate_" + id).html(string)  
  var slider = document.getElementById("myRange");
  $("#card_button").html("Donate $" + slider.value)
  slider.oninput = function() {
  $("#card_button").html("Donate $" + slider.value) 
  }
}

function setHooks(id,string){
    $("#crypto_donate_" + id).html(string)  
    var slider = document.getElementById("myRange");
    var output = document.getElementById("demo");
    output.innerHTML = slider.value;

    slider.oninput = function() {

    output.innerHTML=this.value; 
    }

    displayAnon();

  $( ".coins" ).change(function(){
    $( ".crypto_button" ).prop( "disabled", false);
    displayAnon();
  });

  $("#tax").change(function() {
      if(this.checked) {
          //Do stuff
          $(".anon_address_xmr").hide();
          $(".anon_address_bch").hide();
          $(".anon_address_btc").hide();
          $(".anon_address_wow").hide();
          $('.kyc').show()
          $(".spinner").hide();
          $("#button_qr").hide();   
          $("#donate_qrcode").html("")
          $("#pay_uri").html("")
          $(".message_input").hide()   
        }
  });

  $("#anon").change(function() {
      if(this.checked) {
        //Do stuff
        $(".kyc").hide();
        var id = $(".coins").children(":selected").attr("id")
        $(".anon_address").hide()
        $("div#" + id).show()
        $("#pay_uri").html("")
        $("#donate_qrcode").html("")
        $("#button_qr").show()
        $(".message_input").hide()
      }
  });
}
