/* book.js */

base_url = "http://45.79.176.125";

//------------------------------------------------------------------------------
function init() {


    api_call('/data/get', null, function(response){
        console.log(response);
        //console.log(format("asks=%s, bids=%s",
        //    response['asks'].length, response['bids'].length));

        $('#title').text('QuadrigaCX Order Book');

        //var d = Sugar.Date(Number(response['timestamp']*1000));
        //$('#date').text(d.toString());

        //$('#n-bids').text(response['bids'].length);
        //$('#n-asks').text(response['asks'].length);
        //$('#json-bids').jsonview(response['bids']);
        $('#json-asks').jsonview(response) //['asks']);
    });
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
