$(document).ready(function () {

    $('.payWithRazorPay').click(function (e){
        e.preventDefault();

        var fname = $("[name='fname']").val();
        var lname = $("[name='lname']").val();
        var email = $("[name='email']").val();
        var phone = $("[name='phone']").val();
        var address = $("[name='address']").val();
        var city = $("[name='city']").val();
        var state = $("[name='state']").val();
        var country = $("[name='country']").val();
        var pincode = $("[name='pincode']").val();
        var token = $("[name='csrfmiddlewaretoken']").val();

        if(!fname || !lname || !email || !phone || !address || !city || !state || !country || !pincode) {
            swal("Alert!", "All fields are mandatory", "error");
            return false;
        }
       

        $.ajax({
            method: "GET",
            url: "/proceed-to-pay",
            success: function (response) {
                var options = {
                    "key": "rzp_test_T3Sq4P1VaiSduJ",
                    "amount": response.total_price * 100,
                    "currency": "INR",
                    "name": "Naveen",
                    "description": "Thank you for buying",
                    "image": "images/slider.jpg",
                    "handler": function (responseb){
                        alert(responseb.razorpay_payment_id);
                        data = {
                            "fname": fname,
                            "lname": lname,
                            "email": email,
                            "phone": phone,
                            "address": address,
                            "city": city,
                            "state": state,
                            "country": country,
                            "pincode": pincode,
                            "payment_mode": "Paid by Razorpay",
                            "payment_id": responseb.razorpay_payment_id,
                            "csrfmiddlewaretoken": token
                        }

                        $.ajax({
                            method: "POST",
                            url: "/place-order",
                            data: data,
                            success: function (responsec) {
                                swal("Congratulations!", responsec.status, "success").then((value) => {
                                    window.location.href = '/my-orders';
                                });
                            }
                        });
                    },
                    "prefill": {
                        "name": fname + " " + lname,
                        "email": email,
                        "contact": phone
                    },
                    "theme": {
                        "color": "#3399cc"
                    }
                };
                var rzp1 = new Razorpay(options);
                rzp1.open();
            }
        });
    });
});
