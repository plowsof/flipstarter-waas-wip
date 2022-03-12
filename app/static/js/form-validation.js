// Wait for the DOM to be ready

async function form_validate() {
  $("form[name='donate']").validate({
    rules: {
      comment: "required"
    },
    // Specify validation error messages
    messages: {
      comment: "Please enter your comment"
    },
    // Make sure the form is submitted to the destination defined
    // in the "action" attribute of the form when valid
    submitHandler: function(form) {
      //make the button none-clickable
      $( ".crypto_button" ).prop( "disabled", true );
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

            var typeNumber = 0;
            var errorCorrectionLevel = 'L';
            var qr = qrcode(typeNumber, errorCorrectionLevel);
            qr.addData(payment_uri);
            qr.make();
            $('#donate_qrcode').html(qr.createImgTag());
            $('#donate_qrcode').children("img").css('width', "70%")
            $('#donate_qrcode').children("img").css('height', "auto")
            let comment_tip = `<span class="c_tip"> (Once your donation is in the mempool, your comment will be displayed. You do not have to send the exact amount promised either. Thank you!)`
            //the coin
            $("#pay_uri").html(`<div class="anon_address_${the_coin}">${payment_uri}</div>${comment_tip}`)
         }         
      });
    } 
  });
};

