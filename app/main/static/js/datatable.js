/* datatable.js  */

base_url = "http://45.79.176.125";
num_format = Sugar.Number.format;
abbr = Sugar.Number.abbr;
data_tag = 'routes_new';
raw_data = null;
holdings_tbl_id = 'dt-holdings';
bots_tbl_id = 'dt-bots';
tbl_data = [];
datatable = null;
holdings_fields = [
    {
        column: {title:'_id'},
        columnDef: { targets:0, visible:false},
        data: { k:'_id', sub_k:'$oid', value:function(v) {
            return parseInt(v.substring(0,8),16)*1000}}
    },
    {
        column: { title:'Datetime&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'},
        columnDef: { targets:1 },
        data: { k:'_id', sub_k:'$oid', value:function(v){
            // Convert MongoDB ObjectId->js Date
            return new Date(parseInt(v.substring(0,8),16)*1000).toLocaleString()}
        }
    },
    {
        column: { title:'Exchange' },
        columnDef:{ },
        data: { k:'exchange' }
    },
    {
        column: { title:'Pair' },
        columnDef: { },
        data: { k:'currency', value:function(v){ return v.toUpperCase() } }
    },
    {
        column: { title:'Status' },
        columnDef:{ },
        data: { k:'status', value:function(v){ return v.toTitleCase() } }
    },
    {
        column: { title:'Trades' },
        columnDef: { },
        data: { k:'volume' }
    },
    {
        column: { title:'Price' },
        columnDef: { },
        data: { k:'trades', sub_k:'0', value:function(v){ return '$'+num_format(v['price'],0) } }
    },
    {
        column: { title:'Volume' },
        columnDef: { },
        data: { k:'volume' }
    },
    {
        column: { title:'Cost' },
        columnDef: { },
        data: { k:'cost' }
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
        data: { k:'volume' }
    },
    {
        column: { title:'Revenue' },
        columnDef: { },
        data: { k:'revenue' }
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
            return data? '$'+num_format(data,2) :'' } 
        },
        data: { k:'cad' }
    }
];

//------------------------------------------------------------------------------
function init() {
    showBotSummary();
    showExchSummary();
    holdingsTable();
}

//------------------------------------------------------------------------------
function showBotSummary() {
    api_call(
        '/stats/get',
        null,
        function(response){
            var stats = JSON.parse(response);
            console.log(stats);
            var html = '';

            html += '<h5 class="mt-3">Closed Holdings</h5>';
            html += 'Total: ' + stats['n_hold_closed'] + '<br>';
            html += 'Trades: ' + stats['n_trades']+'<br>';
            html += 'Value: $' + abbr(stats['cad_traded'],0) + ' CAD<br>';
            html += 'Earnings: $' + abbr(stats['earnings'],1) + ' CAD<br>';


            html += '<h5 class="mt-3">Open Holdings</h5>';
            html += 'Total: ' + stats['n_hold_open'] + '<br>';
            html += 'Btc: ' + num_format(stats['btc'],5) + ' ~$'
            + abbr(stats['btc_value'],1) + '<br>';
            html += 'Eth: ' + num_format(stats['eth'],5) + ' ~$'
            + abbr(stats['eth_value'],1) + '<br>';




            $('#stats').html(html);
        }
    );
}

//------------------------------------------------------------------------------
function showExchSummary() {
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
function holdingsTable() {
    api_call(
        '/holdings/get',
        data=null,
        function(response){
            raw_data = JSON.parse(response);
            buildDataTable(
                holdings_tbl_id,
                holdings_fields.map(function(x){
                    return x.column
                }),
                formatData(raw_data));
            applyCss(holdings_tbl_id);
            $('#dt-holdings').prop('hidden',false);
        });
}

//------------------------------------------------------------------------------
function buildDataTable(id, columns, data ) {
    datatable = $('#'+id).DataTable({ //.removeAttr('width').DataTable({
        data: data,
        columns: columns,
        order: [[0,'desc']],
        columnDefs: holdings_fields.map(function(x){ return x.columnDef ? x.columnDef : false; }),
        fixedColumns: true,
        responsive:true,
        select:false,
        lengthMenu: [[10, 50, 100,-1], [10, 50, 100, "All"]]
    });
    //datatable.columns.adjust().draw();
}

//------------------------------------------------------------------------------
function applyCss(_id) {
    var wrap = format('#%s_wrapper', _id);
    var $filtr_row = $(wrap+' .row:nth-child(1)');
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
    $('#filters').prop('hidden',false);

    $pages_row.addClass('pages-row');
    $('.holdings-container').prop('hidden',false)

    $('.dataTables_info').html($('.dataTables_info').html().replace("Showing ",""));

    $('#'+_id).parent().css('padding','0');
    $('#'+_id).parent().css('margin','0');
}

//------------------------------------------------------------------------------
function formatData(data) {
    var get = Sugar.Object.get;

    // Convert response data to datatable data format
    for(var i=0; i<data.length; i++) {
        var route = data[i];
        var tbl_row = [];

        for(var j=0; j<holdings_fields.length; j++) {
            var k = holdings_fields[j]['data']['k'];
            var sub_k = holdings_fields[j]['data']['sub_k'];
            var val = '';

            if(!sub_k && get(route, k))
                val = route[k];
            else if(sub_k && get(route[k], sub_k))
                val = route[k][sub_k];

            if(holdings_fields[j]['data'].hasOwnProperty('value'))
                val = holdings_fields[j]['data']['value'](val);

            tbl_row.push(val);
        }
        tbl_data.push(tbl_row);
    }
    return tbl_data;
}

//------------------------------------------------------------------------------
function filterDates(start, end) {
    var filtered = [];

    for(var i=0; i<raw_data.length; i++) {
        var route = raw_data[i];
        var date = new Date(route['date']['$date']);
        if(start && date < start)
            continue;
        if(end && date > end)
            continue;
        filtered.push(route);
    }

    console.log(format('%s routes filtered between %s to %s',
        filtered.length,
        start ? start.strftime('%b-%d-%Y') : 'anytime',
        end ? end.strftime('%b-%d-%Y') : 'anytime'));
    return filtered;
}

//------------------------------------------------------------------------------
function api_call(path, data, on_done) {
    $.ajax(
        { type:'POST', data:data, url:base_url + path }
    )
    .done(function(response){
        on_done(response);
    })
    .fail(function(response){
        on_done(response)
    });
}
