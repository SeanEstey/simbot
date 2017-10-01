/* main.js  */

BASE_URL = "http://45.79.176.125";
TBL_ID = 'dt-holdings';

num_format = Sugar.Number.format;
abbr = Sugar.Number.abbr;

// Raw holdings data returned from server
gHoldings = null;
// Datatable instance
gDatatable = null;
// Column definitions for holdings datatable
gColumnDefs = [
    {
        column: {title:'Timestamp'},
        columnDef: { targets:0, visible:false},
        data: { k:'_id', sub_k:'$oid', value:function(oid) { return objectIdToTime(oid) } }
    },
    {
        column: { title:'Datetime&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'},
        columnDef: { targets:1 },
        data: { k:'_id', sub_k:'$oid', value:function(oid){ return objectIdToDate(oid).toLocaleString() } }
    },
    {
        column: { title:'Exchange' },
        columnDef:{ },
        data: { k:'exchange' }
    },
    {
        column: { title:'Pair' },
        columnDef: { },
        data: { k:'pair'}
    },
    {
        column: { title:'Status' },
        columnDef:{ },
        data: { k:'status', value:function(v){ return v.toTitleCase() } }
    },
    {
        column: { title:'Trades' },
        columnDef: { },
        data: { k:'trades', value:function(v){ return v.length } }
    },
    {
        column: { title:'Buy Price' },
        columnDef: { },
        data: { k:'trades', sub_k:'0', value:function(v){ return '$'+num_format(v['price'],0) } }
    },
    {
        column: { title:'Buy Volume' },
        columnDef: { },
        data: { k:'trades', value:function(v){ return v[0]['volume'][0]} }
    },
    {
        column: { title:'Cost' },
        columnDef: { },
        data: { k:'trades', value:function(v){ return '$'+v[0]['volume'][1]*-1 } }
    },
    {
        column: { title:'Sell Price (Avg)' },
        columnDef: { },
        data: { k:'trades', value:function(v){ return v.length>1 ?
        '$'+num_format(v[v.length-1]['price'],0) : '' } }
    },
    {
        column: { title:'Balance' },
        columnDef: { },
        data: { k:'trades', value:function(v) {
            var vol_bal=0;
            for(var i=0; i<v.length; i++) {
                vol_bal+=v[i]['volume'][0];
            }
            return num_format(vol_bal,5);
        } }
    },
    {
        column: { title:'Revenue' },
        columnDef: { },
        data: { k:'trades', value:function(v) {
            var rev=0;
            for(var i=1; i<v.length; i++) {
                rev+=v[i]['volume'][1];
            }
            return '$'+num_format(rev,2);
        } }
    },
    {
        column: { title:'Fees' },
        columnDef:{ targets:12, render:function(data, type, row){
            return data? '$'+num_format(data,2) :'' } 
        },
        data: { k:'fees' }
    },
    {
        column: { title:'Net Earning' },
        columnDef:{ targets:13, render:function(data, type, row){
            return row[4]=='Closed'? '$'+num_format(data[1],2) : '' } 
        },
        data: { k:'balance'}
    }
];

//------------------------------------------------------------------------------
function init() {
    showBotSummary();
    showExchTickers();
    showHoldingsTable();
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
        });
}

//------------------------------------------------------------------------------
function buildDataTable(tbl_id, tbl_cols, tbl_col_defs, tbl_data ) {
    gDatatable = $('#'+tbl_id).DataTable({
        data: tbl_data,
        columns: tbl_cols,
        order: [[0,'desc']],
        columnDefs: tbl_col_defs, 
        fixedColumns: true,
        responsive:true,
        select:false,
        lengthMenu: [[10, 50, 100,-1], [10, 50, 100, "All"]]
    });
}

//------------------------------------------------------------------------------
function applyCustomization(_id) {
    var wrap = format('#%s_wrapper', _id);
    var $filtr_row = $(wrap+' .row:nth-child(1)');
    var $tbl_row = $(wrap+' .row:nth-child(2)');
    var $pages_row = $(wrap+' .row:nth-child(3)');

    $filtr_row
        .addClass('d-flex justify-content-between filters-row')
        .removeClass('row');
    $filtr_row.find(' div:nth-child(1)')
        .removeClass('col-md-6 col-sm-12');
    $filtr_row.find(' div:nth-child(2)')
        .removeClass('col-md-6 col-sm-12');
    $('.dataTables_length')
        .removeClass('col-md-9');
    var $a = $('select[name="dt-holdings_length"]').parent();
    $a.html($a.html().replace("Show","").replace("entries"," /Page"))
    $('.dataTables_length label').appendTo($('#filters'));
    $('.dataTables_length').append($('#filters'));
    $('.filters-row').append($('#min-max'));
    $('#min-max').prop('hidden',false);
    $('#filters').prop('hidden',false);

    $tbl_row.prop('id','tbl-row');
    $tbl_row.addClass('collapse show');

    $pages_row.addClass('pages-row');

    $('.holdings-container').prop('hidden',false)
    $('.dataTables_info').html($('.dataTables_info').html().replace("Showing ",""));
    $('#'+_id).parent().css('padding','0');
    $('#'+_id).parent().css('margin','0');

    $('#dt-holdings').prop('hidden',false);

    // Minimize/maximize pane styling
	$('div')
        .on('shown.bs.collapse', function() {

            var id = $(this).prop('id');
            console.log('id='+id+', class='+$(this).prop('class'));
            if(['tbl-row'].indexOf(id) > -1) {
                $('#min-max i')
                    .removeClass('fa-window-maximize')
                    .addClass('fa-window-minimize');
                }
		})
        .on('hidden.bs.collapse', function() {
			var id = $(this).prop('id');
            console.log('id='+id+', class='+$(this).prop('class'));
			if(['tbl-row'].indexOf(id) > -1) {
                $('#min-max i')
                    .removeClass('fa-window-minimize')
                    .addClass('fa-window-maximize');
			}
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
function formatData() {
    var tbl_data = [];
    var get = Sugar.Object.get;

    // Convert response data to datatable data format
    for(var i=0; i<gHoldings.length; i++) {
        var holding = gHoldings[i];
        var tbl_row = [];

        for(var j=0; j<gColumnDefs.length; j++) {
            var k = gColumnDefs[j]['data']['k'];
            var sub_k = gColumnDefs[j]['data']['sub_k'];
            var val = '';

            if(!sub_k && get(holding, k))
                val = holding[k];
            else if(sub_k && get(holding[k], sub_k))
                val = holding[k][sub_k];

            if(gColumnDefs[j]['data'].hasOwnProperty('value'))
                val = gColumnDefs[j]['data']['value'](val);

            tbl_row.push(val);
        }
        tbl_data.push(tbl_row);
    }
    return tbl_data;
}

//------------------------------------------------------------------------------
function filterDates(start, end) {
    var filtered = [];

    for(var i=0; i<data.length; i++) {
        var holdings = data[i];
        var date = new Date(holdings['date']['$date']);
        if(start && date < start)
            continue;
        if(end && date > end)
            continue;
        filtered.push(holdings);
    }

    console.log(format('%s holdingss filtered between %s to %s',
        filtered.length,
        start ? start.strftime('%b-%d-%Y') : 'anytime',
        end ? end.strftime('%b-%d-%Y') : 'anytime'));
    return filtered;
}

//------------------------------------------------------------------------------
function api_call(path, data, on_done) {
    $.ajax(
        { type:'POST', data:data, url:BASE_URL + path }
    )
    .done(function(response){
        on_done(response);
    })
    .fail(function(response){
        on_done(response)
    });
}

//------------------------------------------------------------------------------
function objectIdToDate(oid) {
    /* MongoDB ObjectId->Date */
    return new Date(parseInt(oid.substring(0,8),16)*1000);
}

//------------------------------------------------------------------------------
function objectIdToTime(oid) {
    /* MongoDB ObjectId->Timestamp (ms) */
    return parseInt(oid.substring(0,8),16)*1000;
}
