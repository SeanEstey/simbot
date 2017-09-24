/* datatable.js  */

base_url = "http://45.79.176.125";
num_format = Sugar.Number.format;
data_tag = 'routes_new';
raw_data = null;
holdings_tbl_id = 'dt-holdings';
bots_tbl_id = 'dt-bots';
tbl_data = [];
datatable = null;

holdings_fields = [
    {
        column: { title:'Datetime'},
        columnDef: { targets:0 },
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
        column: { title:'Status' },
        columnDef:{ },
        data: { k:'status', value:function(v){ return v.toTitleCase() } }
    },
    {
        column: { title:'Earnings' },
        columnDef:{ targets:3, render:function(data, type, row){
            return data? '$'+num_format(data,2) :'' } 
        },
        data: { k:'cad' }
    },
    {
        column: { title:'Currency' },
        columnDef: { },
        data: { k:'currency', value:function(v){ return v.toUpperCase() } }
    },
    {
        column: { title:'BTC' },
        columnDef: { },
        data: { k:'btc'},
    },
    {
        column: { title:'ETH' },
        columnDef: { },
        data: { k:'eth' }
    },
    {
        column: { title:'Buy Price' },
        columnDef: { },
        data: { k:'trades', sub_k:'0', value:function(v){ return '$'+num_format(v['price'],0) } }
    },
    {
        column: { title:'Sell Price' },
        columnDef: { },
        data: { k:'trades', value:function(v){ return v.length>1 ?
        '$'+num_format(v[v.length-1]['price'],0) : '' } }
    }
];

//------------------------------------------------------------------------------
function init() {
    
    api_call('/stats/get', null, function(response){
        var stats = JSON.parse(response);
        var html = '';
        html += 'Earnings: $' + num_format(stats['earnings'],2) + ' CAD<br>';
        html += 'Open: ' + stats['n_open'] + '<br>';
        html += 'Closed: ' + stats['n_closed'] + '<br>';
        html += 'BTC: ' + num_format(stats['btc'],5) + ' [~$'
        + num_format(stats['btc_value'],0) + ']<br>';
        html += 'ETH: ' + num_format(stats['eth'],5) + ' [~$'
        + num_format(stats['eth_value'],0) + ']<br>';
        html += 'Net Holdings: $' + num_format(stats['net'],2) + ' CAD';
        
        $('#stats').html(html);
    });

    api_call('/tickers/get', null, function(response){
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
    });

    api_call(
      '/holdings/get',
      data=null,
      function(response){
          raw_data = JSON.parse(response);

          buildDataTable(
            holdings_tbl_id,
            holdings_fields.map(function(x){ return x.column }),
            formatData(raw_data));

          applyCss(holdings_tbl_id);
      });

    // Event handlers
    $('.nav-tabs a').click(function (e){
        e.preventDefault();
        var id = $(this).prop('hash');

        if(id == '#upcoming')
            showUpcoming();
        else if(id == '#historic')
            showHistoric();
    });
}

//------------------------------------------------------------------------------
function buildDataTable(id, columns, data ) {

    datatable = $('#'+id).removeAttr('width').DataTable({
        data: data,
        columns: columns,
        order: [[0,'desc']],
        columnDefs: holdings_fields.map(function(x){ return x.columnDef ? x.columnDef : false; }),
        fixedColumns: true,
        responsive:false,
        select:false,
        lengthMenu: [[10, 50, 100,-1], [10, 50, 100, "All"]]
    });

    datatable.columns.adjust().draw();
}

//------------------------------------------------------------------------------
function applyCss(_id) {

      $('#'+_id).parent().css('padding','0');
      $('#'+_id).parent().css('margin','0');
      var wrapper_id = '#'+_id+'_wrapper';
      $(wrapper_id).css('background-color', 'whitesmoke');
      $(wrapper_id).css('border-top-right-radius', '5px');
      $(wrapper_id + ' .row').first().css('padding', '15px');
      $(wrapper_id + ' .row').first().css('border-bottom', '1px solid rgba(0,0,0,0.12)');
      $(wrapper_id + ' .row').last().css('padding', '.5rem 1.0rem');
      $(wrapper_id + ' .row').last().css('border-top', '1px solid rgba(0,0,0,.12)');
      $(wrapper_id).parent().css('background-color','white');
      $(wrapper_id).css('border','none');
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
function showOpenHoldings() {
    // Flter dates >= today, show/hide appropriate columns

    var today = new Date().clearTime();
    var filtData = filterDates(today, null);
    var titles = fields.map(function(x){return x.column.title});
    var show = ['Status','Unserved','Warnings','Errors'];
    var hide = [
        'Zeros','Donatons','Collect. Rate','Estimate','Receipt','Estimate Avg',
        'Estimate Trend','Estimate Margin','Invoice','Mileage','RA','RA Hrs',
        'Trip Hrs','Driver Hrs','Cages','Vehicle'
    ];
    for(var i=0; i<hide.length; i++)
        datatable.column(titles.indexOf(hide[i])).visible(false);
    for(var i=0; i<show.length; i++)
        datatable.column(titles.indexOf(show[i])).visible(true);

    $('#route-btn').show().prop('disabled',true);
    tbl_data = [];
    datatable.clear();
    datatable.rows.add(formatData(filtData));
    datatable.draw();
}

//------------------------------------------------------------------------------
function showClosedHoldings() {
    // Filter dates < today, show/hide appropriate columns

    var show = [
        'Zeros','Donatons','Collect. Rate','Estimate','Receipt','Estimate Avg',
        'Estimate Trend','Estimate Margin','Invoice','Mileage','RA','RA Hrs',
        'Trip Hrs','Driver Hrs','Cages','Vehicle'
    ];
    var hide = ['Status','Unserved','Warnings','Errors'];
    var titles = fields.map(function(x){return x.column.title});
    for(var i=0; i<show.length; i++)
        datatable.column(titles.indexOf(show[i])).visible(true);
    for(var i=0; i<hide.length; i++)
        datatable.column(titles.indexOf(hide[i])).visible(false);
        
    $('#route-btn').hide();
    tbl_data = [];
    datatable.clear();
    datatable.rows.add(
        formatData(
            filterDates(null, new Date().clearTime())));
    datatable.draw();
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

/*fields = [
    { column:{ title:'Timetamp' }, columnDef:{ targets:0, visible:false, searchable:false }, data:{ k:'date', sub_k:'$date' } },
    { column:{ title:'Select' }, columnDef:false, data:false },
    { column:{ title:'Date&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;', width:"15%" },
      columnDef:{ targets:2, width:"15%" }, data:{ k:'date', sub_k:'$date', value:function(v){ return new Date(v).strftime('%b %d %Y') } } },
    { column:{ title:'Block' }, columnDef:false, data:{ k:'block', sub_k:false } },
    { column:{ title:'Size' }, columnDef:false, data:{ k:'stats', sub_k:'nBlockAccounts' } },
    { column:{ title:'Skips' }, columnDef:false, data:{ k:'stats', sub_k:'nSkips' } },
    { column:{ title:'Orders' }, columnDef:false, data:{ k:'stats', sub_k:'nOrders' } },
    { column:{ title:'Zeros' }, columnDef:false, data:{ k:'stats', sub_k:'nZeros' } },
    { column:{ title:'Donations' }, columnDef:false, data:{ k:'stats', sub_k:'nDonations' } },
    { column:{ title:'Collect. Rate' }, columnDef:false, 
      data:{ k:'stats', sub_k:'collectionRate', value:function(v){ return typeof(v)=='number'? num_format(v*100,1)+'%':'' } } },
    { column:{ title:'Estimate' }, data:{ k:'stats', sub_k:'estimateTotal' },
      columnDef:{ targets:10, render:function(data, type, row){ return data? '$'+num_format(data,2) :'' } } },
    { column:{ title:'Receipt' }, data:{ k:'stats', sub_k:'receiptTotal' },
      columnDef:{ targets:11, render:function(data, type, row){ return data? '$'+num_format(data,2) :'' } } },
    { column:{ title:'Estimate Avg' }, data:{ k:'stats', sub_k:'estimateAvg' },
      columnDef:{ targets:12, render:function(data,type,row){ return data? '$'+num_format(data,2) :'' } } },
    { column:{ title:'Estimate Trend' }, columnDef:false,
      data:{ k:'stats', sub_k:'estimateTrend', value:function(v){ return v? '$'+num_format(v,2) :'' } } },
    { column:{ title:'Estimate Margin' }, columnDef:false,
      data:{ k:'stats', sub_k:'estimateMargin', value:function(v){ return typeof(v)=='number'? num_format(v*100,1)+'%' :'' } } },
    { column:{ title:'Status' }, columnDef:false, data:{ k:'routific', sub_k:'status'} },
    { column:{ title:'Unserved' }, columnDef:false, data:{ k:'routific', sub_k:'nUnserved'} },
    { column:{ title:'Warnings' }, columnDef:false, data:{ k:'routific', sub_k:'warnings', value:function(v){ return typeof(v) == 'object'? v.length : '' }} },
    { column:{ title:'Errors' }, columnDef:false, data:{ k:'routific', sub_k:'errors', value:function(v){ return typeof(v) == "object"? v.length : '' } } },
    { column:{ title:'Depot' }, columnDef:false, data:{ k:'routific', sub_k:'depot', value:function(v){ return v.name? v.name : ''} } },
    { column:{ title:'Driver' }, columnDef:false, data:{ k:'driverInput', sub_k:'driverName', value:function(v){ return v? v : ''} } },
    { column:{ title:'Invoice' }, columnDef:false, data:{ k:'driverInput', sub_k:'invoiceNumber'} },
    { column:{ title:'Mileage' }, columnDef:false, data:{ k:'driverInput', sub_k:'mileage'} },
    { column:{ title:'RA' }, columnDef:false, data:{ k:'driverInput', sub_k:'raName'}, },
    { column:{ title:'Vehicle' }, columnDef:false, data:{ k:'driverInput', sub_k:'vehicle' } },
    { column:{ title:'RA Hrs' }, columnDef:false, data:{ k:'driverInput', sub_k:'raHrs'} },
    { column:{ title:'Trip Hrs' }, columnDef:false, data:{ k:'driverInput', sub_k:'driverTripHrs'} },
    { column:{ title:'Driver Hrs' }, columnDef:false, data:{ k:'driverInput', sub_k:'driverHrs'} },
    { column:{ title:'Vehicle Inspection' }, columnDef:{ targets:28, visible:false }, data:{ k:'driverInput', sub_k:'vehicleInspection'} },
    { column:{ title:'Notes' }, columnDef:{ targets:29, visible:false }, data:{ k:'driverInput', sub_k:'notes'} },
    { column:{ title:'Cages' }, columnDef:false, data:{ k:'driverInput', sub_k:'nCages'} },
    { column:{ title:'Total Duration' }, columnDef:false, data:{ k:'routific', sub_k:'totalDuration', value:function(x){ return x? num_format(x/60,2) : '' } } }
];*/

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
