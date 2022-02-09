// Wait for the DOM to be ready

async function form_validate() {
  // Initialize form validation on the registration form.
  // It has the name attribute "registration"
  $("form[name='donate']").validate({
    // Specify validation rules
    rules: {
      // The key name on the left side is the name attribute
      // of an input field. Validation rules are defined
      // on the right side
      fname: "required",
      email: {
        required: true,
        // Specify that email should be validated
        // by the built-in "email" rule
        email: true
      },
    },
    // Specify validation error messages
    messages: {
      fname: "Please enter your firstname",
      email: "Please enter a valid email address"
    },
    // Make sure the form is submitted to the destination defined
    // in the "action" attribute of the form when valid
    submitHandler: function(form) {
      $(".spinner").show()
      $("#donate_qrcode").html("")
      $("#pay_uri").html("")
      var id = $(".coins").children(":selected").attr("id").split("_")[1]
      form_data = $(form).serialize()
      form_data = form_data + "&uid=" + id
      console.log(form_data)
      //we can send a uid - to link the payment to a specific wish e.g. + "&uid=${id}"
                   $.ajax({
          url: form.action,
          type: form.method,
          data: form_data,
         success: function(data){
          $(".spinner").hide()
            $("#donate_qrcode").html("")
            split_me = form_data.split("coins")
            let the_coin = split_me[1].substring(1, 4)
            //amount=1&coins=xmr&choice=tax&fname=asdca&street=asdca&zip=asdc&email=asdadc%40lol.com
            //1&coins=xmr&choice=tax&fname=asdca&street=asdca&zip=asdc&email=asdadc%40lol.com

            split_amount = form_data.split("amount=")
            usd_amount = split_amount[1].split("&")[0]
            let uri = ""
            let coin_price = ""
            let symbol = ""

            if (the_coin == "xmr") {
              uri = "monero:"
              str_amount = "tx_amount"
              symbol = "monero"
              //?tx_amount=239
            } else if (the_coin == "bch"){
              uri = "bitcoincash:"
              str_amount = "amount"
              symbol = "bitcoin-cash"
            } else {
              uri = "bitcoin:"
              str_amount = "amount"
              symbol = "bitcoin"
            }
            
            //price of coin / amount
            the_price = getPriceSingle(symbol)
            total_coins = usd_amount / the_price 
            data = JSON.parse(data)
            //alert(data["address"])
            payment_uri = uri + data.address + "?" + str_amount + "=" + total_coins.toFixed(12)
            $("#donate_qrcode").ClassyQR({
              create: true,
              type: 'text',
              text: payment_uri
            });
            $("#pay_uri").html(payment_uri)
         }         
      });
    } 
  });
};

async function card_validate() {
  // Initialize form validation on the registration form.
  // It has the name attribute "registration"
  $("form[name='card_donate']").validate({
    // Specify validation rules
    rules: {
      // The key name on the left side is the name attribute
      // of an input field. Validation rules are defined
      // on the right side
      fname: "required",
      email: {
        required: true,
        // Specify that email should be validated
        // by the built-in "email" rule
        email: true
      },
    },
    // Specify validation error messages
    messages: {
      fname: "Please enter your firstname",
      email: "Please enter a valid email address"
    },
    // Make sure the form is submitted to the destination defined
    // in the "action" attribute of the form when valid
    submitHandler: function(form) {
      //alert("hello")
      id = $("form[name='card_donate']").attr("id")
      usd = $("#myRange").val() * 100
      console.log(id)
      console.log(usd)
      var data = ( $(form).serializeArray() );
      send_this = {
        "fname": data[0]["value"],
        "lname": data[1]["value"],
        "street": data[2]["value"],
        "zip": data[3]["value"],
        "email": data[4]["value"],
        "id": id,
        "usd": usd
      }
      console.log(send_this)
      $.ajax({
        url: "/flask/fiat_donate",
        type: "POST",
        data: JSON.stringify(send_this),
        contentType: "application/json; charset=utf-8",
        success: function(data){
          $(".spinner").hide()
          //alert("success")
          window.location.href = data
        }
      });
      //[{"name":"fname","value":"aaaa"},{"name":"fname","value":""},{"name":"street","value":"aaa@lo..com"},{"name":"zip","value":"aaa"},{"name":"email","value":"aaa@lol.com"}]
    } 
  });
};

function fiatSubmit(id){
  $.ajax({

  url: "/flask/fiat_donate",
  type: "POST",
  data: JSON.stringify({"wish_id":id,"usd_amount":usd_amount, "uuid": "someid"}),
  contentType: "application/json; charset=utf-8",
  success: function(data){
  $(".spinner").hide()
  window.location.href = data
  }
})};



async function ticket_validate() {
  // Initialize form validation on the registration form.
  // It has the name attribute "registration"
  $(".spinner_ticket").hide()
  $("form[name='buy_ticket']").validate({
    // Specify validation rules
    rules: {
      // The key name on the left side is the name attribute
      // of an input field. Validation rules are defined
      // on the right side
      fname: "required",
      email: {
        required: true,
        // Specify that email should be validated
        // by the built-in "email" rule
        email: true
      },
    },
    // Specify validation error messages
    messages: {
      fname: "Please enter your firstname",
      email: "Please enter a valid email address"
    },
    // Make sure the form is submitted to the destination defined
    // in the "action" attribute of the form when valid
    submitHandler: function(form) {
      $(".spinner_ticket").show()
      $("#donate_qrcode_ticket").html("")
      $("#pay_uri_ticket").html("")
      form_data = $(form).serialize()
      let ticket_type = standard
      if($('input#standard').is(':checked')){
        ticket_type = "ticket"
      }else{
        ticket_type = "ticket_vip"
      }
      form_data += `&uid=${ticket_type}&choice=tax`
      if ($('input.checkbox_ticket').is(':checked')){
        form_data += "&consent=1"
      }else{
        form_data+="&consent=0"
      }
       $.ajax({
          url: form.action,
          type: form.method,
          data: form_data,
         success: function(data){
            $(".spinner_ticket").hide()
            $("#donate_qrcode_ticket").html("")
            split_me = form_data.split("coins")
            let the_coin = split_me[1].substring(1, 4)
            let uri = ""
            let coin_price = ""
            let symbol = ""

            if (the_coin == "xmr") {
              uri = "monero:"
              str_amount = "tx_amount"
              symbol = "monero"
              //?tx_amount=239
            } else if (the_coin == "bch"){
              uri = "bitcoincash:"
              str_amount = "amount"
              symbol = "bitcoin-cash"
            } else {
              uri = "bitcoin:"
              str_amount = "amount"
              symbol = "bitcoin"
            }
            
            //price of coin / amount
            data = JSON.parse(data)
            //alert(data["address"])
            payment_uri = uri + data.address + "?" + str_amount + "=" + data.amount_expected
            $("#donate_qrcode_ticket").ClassyQR({
              create: true,
              type: 'text',
              text: payment_uri
            });
            $("#pay_uri_ticket").html(payment_uri)
         }         
      });
      //we can send a uid - to link the payment to a specific wish e.g. + "&uid=${id}"
    } 
  });
};
//coins=xmr&ticket=standard&quantity=1&fname=a&email=a%40lol.com&uid=ticket&choice=tax&consent=1
