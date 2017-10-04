/* main.js  */

num_format = Sugar.Number.format;
abbr = Sugar.Number.abbr;
BASE_URL = "http://45.79.176.125";
TBL_ID = 'dt-holdings';
gHoldings = null; // Raw holdings data returned from server
gDatatable = null; // Datatable instance
$mktPanl = $('#markets');
$hldPanl = $('#holdings');

//------------------------------------------------------------------------------
function initMain() {
    initSlidePanel('holdings');
    initSlidePanel('markets');
    initChart('chart-contr','spinner');
    initEventHandlers();
    showBotSummary();
    showExchTickers();
    showHoldingsTable();
    renderMarketChart();
}

//------------------------------------------------------------------------------
function initEventHandlers() {
    $('#markets select').change(function(){
        renderMarketChart();
	});

    $(window).resize(function(){
        // Adjust side frame height to 100%
        $('#side_frm').height($(window).height() - $(".banner").height());
        resizeChart();
    })
    $(window).resize();
}

//------------------------------------------------------------------------------
function renderMarketChart() {
    showSpinner(true);
    var span_name = $('#markets select[name="timespan"]').val();

    api_call('/trades/get',
        data={
            exchange: $('#markets select[name="exchange"]').val(),
            asset: $('#markets select[name="asset"]').val(),
            since: getTimespan(span_name, units='sec')['since'],
            until: getTimespan(span_name, units='sec')['until']
        },
        function(resp) {
            drawChart(JSON.parse(resp), span_name, timespans[span_name]);
        }
    );
}

//------------------------------------------------------------------------------
function showBotSummary() {
    api_call(
        '/stats/get',
        null,
        function(response){
            var stats = JSON.parse(response);
            $('#earnings').html('$'+abbr(stats['earnings'],1));
            $('#cad_traded').html('$'+abbr(stats['cad_traded'],1));
            $('#btc').html(num_format(stats['btc'],5));
            $('#eth').html(num_format(stats['eth'],5));
            $('#n_hold_open').html(num_format(stats['n_hold_open']));
            $('#n_hold_closed').html(num_format(stats['n_hold_closed']));
            $('#n_trades').html(num_format(stats['n_trades']));
        }
    );
}

//------------------------------------------------------------------------------
function showExchTickers() {
    api_call(
        '/tickers/get',
        null,
        function(response){
            var tickers = JSON.parse(response);
            tickers.sort(function(a,b) {
                var name_a = a.name.toUpperCase();
                var name_b = b.name.toUpperCase();
                if(name_a < name_b) return -1;
                if(name_a > name_b) return 1;
                return 0;
            });

            for(var i=0; i<tickers.length; i++) {
                var book = tickers[i];
                delete book['_id'];
                var t_id = '#ticker'+(i+1);
                var $item = $('#ticker-item').clone().prop('id',t_id);
                $item.find('#exch').text(book['name']);
                $item.find('#trade-pair').text(book['base'].toUpperCase()+'/'+book['trade'].toUpperCase());
                $item.find('#bid').text('$' + num_format(book['bid'],0));
                $item.find('#ask').text('$'+ num_format(book['ask'],0));
                $item.find('#low').text('$'+ num_format(book['low'] || "",0));
                $item.find('#high').text('$'+ num_format(book['high'] || "",0));
                $item.find('#book-json').jsonview(book);
                $('#tickers').append($item);
                $item.find('#book-json .expanded').trigger('click');
                $item.prop('hidden',false);
                $item.click(function() {
                    $(this).find('#book-json').prop('hidden',false);
                });
            }

            // Calculate any arbitrage rates
            var h_bid = null;
            var h_exch = "";
            var l_ask = null;
            var l_exch = "";

            for(var i=0; i<tickers.length; i++) {
                var book = tickers[i];
                if(book['trade'] != 'btc')
                    continue;
                if(!h_bid) {
                    h_bid = book['bid'];
                    h_exch = book['name'];
                    l_ask = book['ask'];
                    l_exch = book['name'];
                    continue;
                }
                else {
                    if(book['bid'] > h_bid) {
                        h_bid = book['bid'];
                        h_exch = book['name'];
                    }
                    if(book['ask'] < l_ask)
                        l_ask = book['ask'];
                        l_exch = book['name'];
                }
            }
            if(l_ask < h_bid) {
                $("#tickers").append("<div>" +
                    "<div>" + l_exch+" <strong>&#8658;</strong> "+h_exch+"</div>" +
                    "<div>Arbitrage: <strong>$"+num_format(h_bid-l_ask,2)+"</strong></div>" +
                "</div>");
            }
        }
    );
}

//------------------------------------------------------------------------------
function showHoldingsTable() {
    api_call(
        '/holdings/get',
        data=null,
        function(response){
            gHoldings = JSON.parse(response);

            buildDataTable(
                TBL_ID,
                gColumnDefs.map(function(x){
                    return x.column
                }),
                gColumnDefs.map(function(x){
                    return x.columnDef ? x.columnDef : false; 
                }),
                formatData()
            );
            applyCustomization(TBL_ID);
            calcSimDuration();
            ///resizeCanvas();
        });
}

//------------------------------------------------------------------------------
function calcSimDuration() {
    var start = objectIdToDate(gHoldings[0]['_id']['$oid']);
    var end = objectIdToDate(gHoldings[gHoldings.length-1]['_id']['$oid']);
    var duration = (end.getTime()-start.getTime())/1000/3600;
    $('#duration').text($('#duration').text() + ' ' + num_format(duration,1) + ' Hrs');
}
