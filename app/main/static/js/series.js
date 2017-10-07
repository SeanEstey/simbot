/* series.js */
X_AXIS_PERIODS = 144;
DAY_MS = 86400000;
TIME_LEN = {
    '1d':DAY_MS,
    '7d':DAY_MS*7,
    '1m':DAY_MS*30,
    '3m':DAY_MS*90,
    '6m':DAY_MS*180,
    '1y':DAY_MS*360
};

/* example series array
[{'label':'Coinsquare', 'asset':'btc', 'time_lbl':'1d', 'data':[]},
{'label':'QuadrigaCX', 'asset':'btc', 'time_lbl':'1d', 'data':[]}]*/
series = [];

//------------------------------------------------------------------------------
function drawSeries() {
    destroyCharts();
    var labels = ykeys = series.map(function(x){return x.label});
    createChart(combineSeries(), 'time', ykeys, labels);
}

//------------------------------------------------------------------------------
function combineSeries() {
    if(series.length < 1)
        return;

    var span = getTimespan(series[0]['time_lbl'], units='ms');
    var period_len = (span[1]-span[0]) / X_AXIS_PERIODS; 
    var data = [];

    // Create datapoints by combining series data for each time period.
    for(var i=0; i<X_AXIS_PERIODS; i++) {
        var start = span[0] + (i*period_len);
        var end = start + period_len;
        var point = { 'time':start };
        for(var j=0; j<series.length; j++) {
            var average = avgPrice(series[j]['data'], start, end);
            point[series[j]['label']] = average;
        }
        data.push(point);
    }
    fillDataGaps(data);
    return data;
}

//------------------------------------------------------------------------------
function getSeriesIdx(series_lbl=false, selected_by=false) {
    var k = v = null;
    if(typeof series_lbl !== 'undefined') {
        k = 'label';
        v = series_lbl;
    }
    else if(typeof selected_by !== 'undefined') {
        k = 'selected_by';
        v = selected_by;
    }
    for(var idx=0; idx<series.length; idx++) {
        if(series[idx][k] == v) return idx;
    }
    return -1;
}

//------------------------------------------------------------------------------
function querySeriesData(label, asset, time_lbl, handler) {
    /* Synchronous POST request returning series data  */
    var data = null;
    var tspan = getTimespan(time_lbl, units='s');
    $.ajax({
        type: 'POST',
        url: BASE_URL + '/trades/get',
        data:{exchange:label, asset:asset, since:tspan[0], until:tspan[1]},
        async:true,
        success:function(resp){ handler(JSON.parse(resp)) }
    });
}

//------------------------------------------------------------------------------
function rmvSeries(idx) {
    series.splice(idx,1);
    drawSeries();
}

//------------------------------------------------------------------------------
function addSeries(label, asset, time_lbl) {
    querySeriesData(label, asset, time_lbl, function(data) {
        series.push({label:label, asset:asset, time_lbl:time_lbl, data:data});
        drawSeries();
    });
}

//------------------------------------------------------------------------------
function replaceSeries(idx, label, asset, time_lbl) {
    querySeriesData(label, asset, time_lbl, function(data) {
        series[idx] = {label:label, asset:asset, time_lbl:time_lbl, data:data};
        drawSeries();
    });
}

//------------------------------------------------------------------------------
function getTimespan(lbl, units='ms') {
    /* @lbl: series duration label ('1d','7d','6m',etc)
     * @units: result format. 'ms' or 's'
     * Returns: array of ints [t_start, t_end]
    */
    var length = null;
    var today = new Date();
    var end = t_now = today.getTime();
    if(lbl == 'ytd')
        length = DAY_MS * (today.getWeek()*7 + today.getDay());
    else
        length = TIME_LEN[lbl];
    var start = length ? (t_now - length) : null;
    return units == 'ms' ? [start, end] : [msToSec(start), msToSec(end)];
}

//------------------------------------------------------------------------------
function avgPrice(data, start, end) {
    /* Price average within time period
    */
    var prices = data.filter(
        function(elem, j, data) {
            var d = elem['date']['$date'];
            if(d >= start && d < end) return elem;
        }
    ).map(function(x) { return x.price });

    if(prices.length == 0)
        return null;
    else
        return Number((prices.reduce(function(a,b){
            return a+b 
        })/prices.length).toFixed(0))
}

//------------------------------------------------------------------------------
function fillDataGaps(datapoints) {
    for(var i=0; i<datapoints.length; i++) {
        var dp = datapoints[i];
        for(var k in datapoints[i]) {
            if(!datapoints[i][k]) { 
                var last = lastPrice(datapoints, k, i);
                if(last)
                    datapoints[i][k] = last;
                else {
                    datapoints[i][k] = nextPrice(datapoints, k, i);
                }
            }
        }
    }
}

//------------------------------------------------------------------------------
function lastPrice(data, k, idx) {
    for(var i=idx; i>=0; i--) {
        if(data[i][k])
            return data[i][k];
    }
    return null;
}

//------------------------------------------------------------------------------
function nextPrice(data, k, idx) {
    for(var i=idx; i<data.length; i++) {
        if(data[i][k])
            return data[i][k];
    }
}
