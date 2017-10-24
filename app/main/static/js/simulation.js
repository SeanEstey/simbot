/* simulation.js  */
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
    showBotSummary();
    showTickers();
    showHoldingsTable();
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
        var mainFrameHgt = $('#main_frm').height();
        var winHgt = window.innerHeight;

        if(mainFrameHgt > winHgt)
            $('.left-frame').height(mainFrameHgt - $('.navbar').height());
        else
            $('.left-frame').height(winHgt);
        //$('#side_frm').height($('body').height() - $('.navbar').height());
    })
    //$(window).resize();
}

//------------------------------------------------------------------------------
function showMarketChart() {
    marketChart = new Chart('chart-contr', 'area');
    $('input[name="QuadrigaCX"]').click();

    var data = null;
    var tspan = getTimespan('1d', units='s');
    $.ajax({
        type: 'POST',
        url: BASE_URL + '/indicators/get',
        data:{
            ex:'QuadrigaCX',
            asset:'btc',
            since:tspan[0] + (3600*6), // convert to UTC
            until:tspan[1] + (3600*6) // convert to UTC
        },
        async:true,
        context: this,
        success:function(json){
            var raw = JSON.parse(json);
            var resampled = resampleData('1d', raw);
            marketChart.addSeries(resampled,
                {ex:'QuadrigaCX', asset:'btc', label:'price', ykey:'price', type:'area',
                decimals:2, time_lbl:'1d'});
        }
    });

    /*
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
    */

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
            console.log(stats);
            $('#traded').html('$'+abbr(stats['traded'],1));
            upd_val($('#cad'), '$'+abbr(stats['cad'],1));
            upd_val($('#btc'), num_format(stats['btc'],5));
            upd_val($('#eth'), num_format(stats['eth'],5));
        }
    );
}

//------------------------------------------------------------------------------
function holdingsStats() {
    upd_val($('#n_trades'), num_format(gHoldings.length));

    var net_earn = n_open = n_close = 0;
    for(var i=0; i<gHoldings.length; i++) {
        var hold = gHoldings[i];
        if(hold['status'] == 'open') {
            n_open++;
        }
        else {
            net_earn += hold['revenue'] - hold['cost'] - hold['fees'];
            n_close++;
        }
    }

    upd_val($('#n_hold_open'), num_format(n_open));
    upd_val($('#n_hold_closed'), num_format(n_close));
    upd_val($('#earnings'), '$'+abbr(net_earn,1));
}

//------------------------------------------------------------------------------
function showTickers() {
    return;
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
            holdingsStats();
            //calcSimDuration();
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
    //$elem.css('background-color','rgba(255,255,0,1.0');
    //$elem.animate({'background-color':'rgba(255,255,255,0.0)'},1000);
}
