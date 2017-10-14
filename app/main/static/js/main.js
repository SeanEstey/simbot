/* main.js  */
num_format = Sugar.Number.format;
abbr = Sugar.Number.abbr;
BASE_URL = "http://45.79.176.125";
TBL_ID = 'dt-holdings';
gHoldings = null; // Raw holdings data returned from server
gDatatable = null; // Datatable instance
$mktPanl = $('#markets');
$hldPanl = $('#holdings');
marketChart = null;
orderBookCharts = null;

//------------------------------------------------------------------------------
function initMain() {
    initSlidePanel('holdings');
    initSlidePanel('markets');
    initSlidePanel('orders');
    initSlidePanel('orders2');

    showBotSummary();
    showExchTickers();
    showHoldingsTable();
    showOrderBookCharts();
    showMarketChart();

    initEventHandlers();
    initSocketIO();
}

//------------------------------------------------------------------------------
function initSocketIO() {
    socket = io.connect('http://45.79.176.125');
    socket.on('connect', function(){
        console.log('socket.io connected!');
    });
    socket.on('updateHoldings', function(data){
        console.log('event=updateHoldings');
        showHoldingsTable();
    });
    socket.on('updateTickers', function(data){
        console.log('event=updateTickers');
        showExchTickers();
    });
    socket.on('updateBot', function(data){
        console.log('event=updateBot');
        showBotSummary();
    });
}

//------------------------------------------------------------------------------
function initEventHandlers() {
    $(window).resize(function(){
        // Adjust side frame height to 100%
        $('#side_frm').height($('#main_frm').height());// - $(".navbar").height());
    })
    $(window).resize();
}

//------------------------------------------------------------------------------
function showOrderBookCharts() {
    orderBookCharts = new Chart('ord-chrt-contr', 'Area');
    orderBookCharts.toggleSpinner(true);
    orderBookCharts.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'v_ask', ykey:'v_ask', type:'line', decimals:3, time_lbl:'1d'}
    );
    orderBookCharts.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bid', ykey:'v_bid', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders2Chart = new Chart('orders2-cont', 'Area');
    orders2Chart.toggleSpinner(true);
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid', ykey:'bid', type:'area', decimals:2, time_lbl:'1d'}
    );
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask', ykey:'ask', type:'area', decimals:2, time_lbl:'1d'}
    );
    orders3Chart = new Chart('orders3-cont', 'Area');
    orders3Chart.toggleSpinner(true);
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders4Chart = new Chart('orders4-cont', 'Area');
    orders4Chart.toggleSpinner(true);
    orders4Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'buy_rate', ykey:'buy_rate', type:'area', decimals:2, time_lbl:'1d'}
    );
    $(window).resize(function(){
        orderBookCharts.resize();
        orders2Chart.resize();
        orders3Chart.resize();
        orders4Chart.resize();
    })
}

//------------------------------------------------------------------------------
function showMarketChart() {
    marketChart = new Chart('chart-contr', 'Area');
    $('#markets input[type="checkbox"]').change(function() {
        var time_lbl = $('#markets select[name="time_lbl"]').val();
        var asset = $('#markets select[name="asset"]').val();
        var series_lbl = $(this).prop('name');
        if($(this)[0].checked) {
            marketChart.toggleSpinner(true);
            marketChart.addSeries(
              '/trades/get',
              {ex:series_lbl, asset:asset, label:series_lbl, ykey:'price', type:'area', decimals:2, time_lbl:time_lbl}
            );
        }
        else if(!$(this)[0].checked) {
            marketChart.toggleSpinner(true);
            var idx = marketChart.getSeriesIdx(series_lbl);
            marketChart.rmvSeries(idx);
        }
    });
    $('#markets select').change(function(){
        marketChart.toggleSpinner(true);
        var time_lbl = $('#markets select[name="time_lbl"]').val();
        var asset = $('#markets select[name="asset"]').val();

        for(var idx=0; idx<marketChart.series.length; idx++) {
            var ex = marketChart.series[idx]['label'];
            marketChart.replaceSeries(
                '/trades/get', 
                {ex:ex, asset:asset, label:ex, asset:asset, ykey:'price', type:'area', decimals:2, time_lbl:time_lbl},
                idx);
        }
    });
    $('input[name="QuadrigaCX"]').click();
    $(window).resize(function(){
        marketChart.resize();
    })
}

//------------------------------------------------------------------------------
function showBotSummary() {
    api_call('/stats/get',
        null,
        function(response){
            var stats = JSON.parse(response);
            $('#earnings').html('$'+abbr(stats['earnings'],1));
            $('#cad_traded').html('$'+abbr(stats['cad_traded'],1));
            upd_val($('#btc'), num_format(stats['btc'],5));
            upd_val($('#eth'), num_format(stats['eth'],5));
            upd_val($('#n_hold_open'), num_format(stats['n_hold_open']));
            upd_val($('#n_hold_closed'), num_format(stats['n_hold_closed']));
            upd_val($('#n_trades'), num_format(stats['n_trades']));
        }
    );
}

//------------------------------------------------------------------------------
function showExchTickers() {
    api_call('/tickers/get',
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

            $('#tickers').empty();

            for(var i=0; i<tickers.length; i++) {
                var book = tickers[i];
                delete book['_id'];
                var t_id = '#ticker'+(i+1);
                var $item = $('#ticker-item').clone().prop('id',t_id);
                $item.find('#exch').text(book['name']);
                $item.find('#trade-pair').text(book['base'].toUpperCase()+'/'+book['trade'].toUpperCase());
                
                upd_val($item.find('#bid'), '$'+num_format(book['bid'],0));
                upd_val($item.find('#ask'), '$'+num_format(book['ask'],0));
                upd_val($item.find('#low'), '$'+num_format(book['low'] || '',0));
                upd_val($item.find('#high'), '$'+num_format(book['high'] || '',0));

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
    api_call('/holdings/get',
        data=null,
        function(response){
            gHoldings = JSON.parse(response);
            buildDataTable(
                TBL_ID,
                gColumnDefs.map(function(x){ return x.column }),
                gColumnDefs.map(function(x){ return x.columnDef ? x.columnDef : false; }),
                formatData()
            );
            applyCustomization(TBL_ID);
            calcSimDuration();
        });
}

//------------------------------------------------------------------------------
function calcSimDuration() {
    var start = objectIdToDate(gHoldings[0]['_id']['$oid']);
    var end = objectIdToDate(gHoldings[gHoldings.length-1]['_id']['$oid']);
    var duration = (end.getTime()-start.getTime())/1000/3600;
    $('#duration').text($('#duration').text() + ' ' + num_format(duration,1) + ' Hrs');
}

//------------------------------------------------------------------------------
function upd_val($elem, val) {
    $elem.html(val);
    $elem.css('background-color','rgba(255,255,0,1.0');
    $elem.animate({'background-color':'rgba(255,255,255,0.0)'},1000);
}
