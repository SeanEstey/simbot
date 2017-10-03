/* datatable.js */

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
            return row[4]=='Closed'? '$'+num_format(data[1]-row[12],2) : '' } 
        },
        data: { k:'balance'}
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
