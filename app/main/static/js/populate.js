/* populate.js */

base_url = "http://45.79.176.125";

//------------------------------------------------------------------------------
function init() {

    api_call('/tickers', null, function(response){
        var tickers = JSON.parse(response);
        console.log(tickers);
    });
    
    api_call('/orders', null, function(response){
        var orders = JSON.parse(response);
        console.log(orders);

        // Insert into orders table
    });
    
    api_call('/trades', null, function(response){
        var trades = JSON.parse(response);
        console.log(trades);
        
        for(var i=0; i<trades.length; i++) {
            // Build trades datatable
        
        }
        // Insert into trades table
    });

    /*api_call('/data/get', null, function(response){
        response = JSON.parse(response);
        console.log(response);
        $('#title').text('Simbot');

        for(var i=0; i<response['exchanges'].length; i++) {
            var ex = response['exchanges'][i];

            if(ex.name != "QuadrigaCX")
                continue

            $('#last').html('$'+ex['last']);
            $('#bid').text('$'+ex['orders']['bids'][0][0])
            $('#ask').text('$'+ex['orders']['asks'][0][0]);

            $('#n-quadcx-bids').text(ex['orders']['bids'].length);
            $('#quadcx-bids').jsonview(ex['orders']['bids']);
            $('#quadcx-bids .expanded').first().trigger('click');
            $('#n-quadcx-asks').text(ex['orders']['asks'].length);
            $('#quadcx-asks').jsonview(ex['orders']['asks']);
            $('#quadcx-asks .expanded').first().trigger('click');
        }
    });*/
}

//------------------------------------------------------------------------------
function getData() {



}

//------------------------------------------------------------------------------
function api_call(path, data, on_done) {
    
    $.ajax(
        { type:'POST', data:data, url:base_url + '/' + path }
    )
    .done(function(response){
        on_done(response);
    })
    .fail(function(response){
        on_done(response)
    });
}
