/* series.js */

X_AXIS_PERIODS = 144;
DAY_MS = 86400000;
timespans = {
    '1d':DAY_MS,
    '7d':DAY_MS*7,
    '1m':DAY_MS*30,
    '3m':DAY_MS*90,
    '6m':DAY_MS*180,
    '1y':DAY_MS*360,
    'ytd':ytdLength(),
    'all':null
};

//------------------------------------------------------------------------------
function ytdLength() {
    var now = new Date();
    return DAY_MS*(now.getWeek()*7 + now.getDay());
}

//------------------------------------------------------------------------------
function toSeconds(time) {
    return Number((time/1000).toFixed(0));
}

//------------------------------------------------------------------------------
function getTimespan(name, units='ms') {
    var time = new Date().getTime();
    var timespan = timespans[name];
    var result = {'since':time-timespan, 'until':time}
    if(units=='sec') {
        result['since'] = toSeconds(result['since']);
        result['until'] = toSeconds(result['until']);
    }
    return result;
}

//------------------------------------------------------------------------------
function avgPrice(data, start, end) {
    /* Price average within time period
    */
    var in_period = data.filter(function(elem, j, data) {
        var d = elem['date']['$date'];
        if(d >= start && d < end)
            return elem['price'];
    });
    var p = in_period.map(function(x){ return x.price });
    if(p.length == 0)
        return 0;
    var avg = p.reduce(function(a,b){ return a+b }) / p.length;
    return Number(avg.toFixed(0));
}

//------------------------------------------------------------------------------
function lastPrice(series, idx) {
    for(var i=idx; i>=0; i--) {
        if(series[i]['price'] > 0)
            return series[i]['price'];
    }
    return 0;
}

//------------------------------------------------------------------------------
function periodize(data, name, timespan) {
    console.log('periodizing data, timespan='+name+', n_datapoints='+data.length+', timespan='+timespan);

    // Divide x-axis into 1440 equal length time periods
    var time = new Date().getTime();
    var step_len = timespan/X_AXIS_PERIODS; 
    var t_first = new Date(time - timespan).getTime();
    var series = [];

    // Get avg price for each period.
    for(var i=0; i<X_AXIS_PERIODS; i++) {
        var t_start = t_first + (i*step_len);
        var avg = avgPrice(data, t_start, t_start + step_len);
        series.push({ price:avg, time:t_start });
    }

    // Fill in missing period gaps
    for(var i=0; i<series.length; i++) {
        if(series[i]['price'] == 0)
            series[i]['price'] = lastPrice(series,i);
    }
    return series;
}

//------------------------------------------------------------------------------
function data_range(series) {
    var prices = series.map(function(x){ return x.price});
    var min = Number(Math.min.apply(null,prices).toFixed(0));
    var max = Number(Math.max.apply(null,prices).toFixed(0));
    var spread = max - min;
    return {'min':min, 'max':max, 'spread':spread};
}
