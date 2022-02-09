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
  } else {
    uri = "bitcoin:"
    str_amount = "amount"
    symbol = "bitcoin"
  }
  price = getPriceSingle(symbol)

  total_coins = usd_value / price
  //draw spinner
  
  $("#donate_qrcode").html("")
  //draw qr code
  address = $(".anon_address_" + coin).text()
  payment_uri = uri + address + "?" + str_amount + "=" + total_coins.toFixed(12)
  $("#donate_qrcode").ClassyQR({
    create: true,
    type: 'text',
    text: payment_uri
  });
  $(".spinner").hide()

  $("#pay_uri").html(`<a href="${payment_uri}">Launch in wallet</a> 1 ${coin} = $${price}`)
}

function getPriceSingle(symbol){
    //alert(symbol)

  let ran_int = Math.floor(Math.random() * 100000)
  //alert(array_prices.length)
  let url_get = `https://api.coingecko.com/api/v3/simple/price?ids=${symbol}&vs_currencies=usd&uid=` + ran_int
  try {
       $.ajax({
          async: false,
          type: 'GET',
          url: url_get,
          success: function(data) {
              //callback
              price = data[symbol]["usd"]
          }
      });
       return price
  }catch (error){
      console.log(error)
      return null;
  }

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

    output.value=this.value; 
    }

    displayAnon();

  $( ".coins" ).change(function(){
    displayAnon();
  });
  // this is the id of the form
  $("#donate").submit(function(e) {

      e.preventDefault(); // avoid to execute the actual submit of the form.

      var form = $(this);
      var url = form.attr('action');
      
      //disable the card button
      $.ajax({
             type: "POST",
             url: url,
             data: form.serialize(), // serializes the form's elements.
             success: function(data)
             {
                $("#donate_qrcode").html("")
                $("#donate_qrcode").ClassyQR({
              create: true,
              type: 'text',
              text: 'monero:' + data["address"] // depends on choice
          });
                $("#pay_uri").html("monero:" + data["address"] + "?blablabla")
             }
           });

      
  });


  $("#tax").change(function() {
      if(this.checked) {
          //Do stuff
          $(".anon_address_xmr").hide();
          $(".anon_address_bch").hide();
          $(".anon_address_btc").hide();
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

  $("#input_comment").change(function()
  {
    if(this.checked){
      $(".message_input").show()
      $('#message_area').prop('placeholder', "hello");
    }
    else{
      $(".message_input").hide()
    }
  });
}
