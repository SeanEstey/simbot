/* datatable.js */
nformat = Sugar.Number.format;

function sformat(value, symbol, decimals) {
    return value ? format('$%s', Sugar.Number.format(value, decimals)) : null;
}

// Column definitions for holdings datatable
gColumnDefs = [
    {
        column: {title:'Timestamp'},
        columnDef: { targets:0, visible:false},
        data: { k:'open_date', sub_k:'$date' }
    },
    {
        column: { title:'Open Date&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'},
        columnDef: { targets:1 },
        data: { k:'open_date', sub_k:'$date', value:function(d){ return new Date(d).toLocaleString() } }
    },
    {
        column: { title:'Exchange' },
        columnDef:{ },
        data: { k:'ex' }
    },
    {
        column: { title:'Pair' },
        columnDef: { },
        data: { k:'pair'}
    },
    {
        column: { title:'Status' },
        columnDef:{ },
        data: { k:'status', value:function(x){ return x.toTitleCase() } }
    },
    {
        column: { title:'Buy Price' },
        columnDef: { },
        data: { k:'buy_price', value:function(x){ return format('$%s', nformat(x,0)) } }  
    },
    {
        column: { title:'Buy Volume' },
        columnDef: { },
        data: { k:'volume', value:function(x){ return nformat(x,5) } }
    },
    {
        column: { title:'Buy Cost' },
        columnDef: { },
        data: { k:'cost', value:function(x){ return format('$%s', nformat(x,2)) } }
    },
    {
        column: { title:'Sell Price (Avg)' },
        columnDef: { },
        data: { k:'sell_price', value:function(x){ return sformat(x,'$',2) } }
    },
    {
        column: { title:'Volume Sold' },
        columnDef: { },
        data: { k:'volume_sold', value:function(x){ return x? nformat(x,5) : '' } }
    },
    {
        column: { title:'Revenue' },
        columnDef: { },
        data: { k:'revenue', value:function(x){ return sformat(x,'$',2) } }
    },
    {
        column: { title:'Fees' },
        columnDef:{ },
        data: { k:'fees', value:function(x){ return sformat(x,'$',2) } }
    },
    {
        column: { title:'Net Earning' },
        columnDef:{ },
        data: { 
            k:null,
            value:function(x) {
                if(x['status'] == 'closed') {
                    var net_earn = x['revenue'] - x['cost'] - x['fees'];
                    return sformat(net_earn, '$', 2);
                } 
                else
                    return '';
            }
        }
    }
];

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

    $tbl_row.prop('id','tbl-row');
    $('#filters').prop('hidden',false);

    $pages_row.addClass('pages-row');

    $('.holdings-container').prop('hidden',false)
    $('.dataTables_info').html($('.dataTables_info').html().replace("Showing ",""));
    $('#'+_id).parent().css('padding','0');
    $('#'+_id).parent().css('margin','0');

    $('#dt-holdings').prop('hidden',false);
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

            if(!k)
                val = holding;
            else if(!sub_k && get(holding, k))
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
