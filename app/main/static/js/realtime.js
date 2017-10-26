// realtime.js
Annotate = Rickshaw.Graph.Annotate;
Legend = Rickshaw.Graph.Legend;
Order = Rickshaw.Graph.Behavior.Series.Order;
Highlight = Rickshaw.Graph.Behavior.Series.Highlight;
RangeSlider = Rickshaw.Graph.RangeSlider;
SeriesToggle = Rickshaw.Graph.Behavior.Series.Toggle;
MS_10_MIN = 600000;
SERIES_CONF = [
    {period: {name:'1d', duration: 86400000}, slices: {amount: 144, duration: 600000}},
    {period: {name:'7d', duration: 604800000}, slices: {amount: 168, duration: 3600000}},
    {period: {name:'1m', duration: 2592000000}, slices: {amount: 240, duration: 10800000}},
    {period: {name:'3m', duration: 7776000000}, slices: {amount: 180, duration: 43200000}},
    {period: {name:'6m', duration: null}, slices: {amount: null, duration: null}},
    {period: {name:'1y', duration: null}, slices: {amount: null, duration: null}},
    {period: {name:'ytd', duration: null}, slices: {amount: null, duration: null}},
    {period: {name:'all', duration: null}, slices: {amount: null, duration: null}}
];

// Globals 
xAxis = yAxis = graph = null;
height = 800;
BASE_URL = "http://45.79.176.125";
ticksTreatment = 'glow';
periodLabel = '1d';
exchange = 'QuadrigaCX';
asset = 'btc';
pair = ['btc','cad'];
ask_min = ask_max = bid_min = bid_max = trade_min = trade_max = 0;
seriesData = {
    'trades':{name:'Trades', scale:null, renderer:'line', color:'steelblue', data:[]},
    'asks': {name:'Asks', renderer:'line', color:'green', data:[]},
    'bids': {name:'Bids', renderer:'line', color:'red', data:[]}
};

//------------------------------------------------------------------------------
function initMain() {
    initGraph();

    socket = io.connect(BASE_URL);
    socket.on('connect', function(){
        console.log('socket.io connected!');
        socket.emit('initGraphData');
    });
    socket.on('updateGraphData', function(response) {
        var data = JSON.parse(response);

        if(data.hasOwnProperty('trades'))
            updateGraphTrades(data['trades']);
        if(data.hasOwnProperty('orderbook'))
            updateGraphOrderBook(data['orderbook']);

        var linearScale = d3.scale.linear().domain([
            Math.min(trade_min, bid_min),
            Math.max(trade_max, ask_max)
        ]);
        var logScale = d3.scale.log().domain([
            Math.min(trade_min, bid_min),
            Math.max(trade_max, ask_max)
        ]);
        seriesData.asks.scale = seriesData.bids.scale = seriesData.trades.scale = logScale;    

        if(!yAxis) {
            yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph:graph,
                orientation:'left',
                tickFormat:Rickshaw.Fixtures.Number.formatKMBT,
                ticksTreatment:ticksTreatment,
                element:getElemById('y_axis'),
                scale:linearScale
            });
            yAxis.render();
        }
        else {
            yAxis.scale = linearScale;
        }

        graph.update();
    });
}

//------------------------------------------------------------------------------
function updateGraphTrades(trades) {
    if(trades[0].ex != exchange || trades[0].pair.join("_") != pair.join("_"))
        return;

    // Reverse array order to chronological
    trades = trades.reverse();

    var data = seriesData.trades.data;
    var v_traded = data.length > 0 ? data.slice(-1)[0].x : 0.0;
    data = data.concat(
        trades.map(function(n) { return {
            x: v_traded+=n.volume,
            y: n.price
        }})
    );
    trade_min = arrDim('min', data.map(obj => obj.y));
    trade_max = arrDim('max', data.map(obj => obj.y));
    var tradeScale = d3.scale.log().domain([trade_min, trade_max]);
    seriesData.trades.data = data;

    console.log(format('new trades=%s, existing=%s', trades.length, seriesData.trades.data.length));
}

//------------------------------------------------------------------------------
function updateGraphOrderBook(data) {
    if(data.ex != exchange || data.pair.join("_") != pair.join("_"))
        return;

    var orders = {asks:data.asks, bids:data.bids};
    // What's the cumulative volume of the trades already graphed?
    var v_cum = v_traded = seriesData.trades.data.slice(-1)[0].x;

    var asks = orders.asks.map(function(n){ return {x:v_cum+=n[1], y:n[0]} });
    ask_min = arrDim('min', asks.map(obj => obj.y));
    ask_max = arrDim('max', asks.map(obj => obj.y));

    v_cum = v_traded;
    var bids = orders.bids.map(function(n){ return {x:v_cum+=n[1], y:n[0]} });
    bid_min = arrDim('min', bids.map(obj => obj.y));
    bid_max = arrDim('max', bids.map(obj => obj.y));

    seriesData.asks.data = asks;
    seriesData.bids.data = bids;

    return;

    // Chop off overly long bid volumes from graph.
    // Find way to do this with logscale instead
    var idx=0;
    for(idx=0; idx<bids.length; idx++) {
        if(bids[idx].x-v_traded > 75) break;
    }
    //if(idx > 0)
    //    bids.splice(idx, bids.length-1);
    //console.log(format('bid_min=%s, bid_max=%s, ask_min=%s, ask_max=%s',
    //    bid_min, bid_max, ask_min, ask_max));
}

//------------------------------------------------------------------------------
function initGraph() {
    graph = new Rickshaw.Graph({
        element: getElemById("chart"),
        height: height,
        renderer: 'line',
        interpolation:'step',
        series: [
            seriesData['trades'],
            seriesData['bids'],
            seriesData['asks']
        ]
    });
    var legend = new Legend(
        {graph:graph, element:getElemById('legend')});
    var toggle = new SeriesToggle(
        {graph:graph, legend:legend});
    var order = new Order(
        {graph:graph, legend:legend});
    var highlighter = Highlight(
        {graph:graph, legend:legend});
    var hoverDetail = new Rickshaw.Graph.HoverDetail(
        {graph:graph, xFormatter:function(x) {return x;}});
    var xAxis = new Rickshaw.Graph.Axis.X({
        graph:graph,
        grid:false
    });
    xAxis.render();
    graph.render();
}

function getElemById(_id){ return document.getElementById(_id); }
function querySelector(name){ return document.querySelector(name); }

//------------------------------------------------------------------------------
function resampleData(period, data) {
    /* Time series data from server is sliced in 10 min intervals, for
     * period=1d. Recalculate for periods [7d,1m,3m,6m,ytd,1y,all].
     * @period: period name
     */
    var conf = get_conf(period);
    var n_subsamples = conf['slices']['duration'] / MS_10_MIN;
    var n_resample_periods = conf['slices']['amount'];
    var resampled = [];

    console.log(format('Resampling data, Period duration=[%s to %s], Num periods=[%s to %s]',
        MS_10_MIN, conf['slices']['duration'], data.length, n_resample_periods));

    for(var i=0; i<n_resample_periods-1; i++) {
        var subsamples = data.splice(0,n_subsamples);

        var sample = {
            ex: subsamples[0]['ex'],
            pair: subsamples[0]['pair'],
            date: subsamples[n_subsamples-1]['end']['$date'],
            start: new Date(subsamples[0]['start']['$date']),
            end: new Date(subsamples[n_subsamples-1]['end']['$date'])
        };
        for(var k in subsamples[0]['avg'])
            sample[k] = [];
        for(var k in subsamples[0]['sum'])
            sample[k] = 0;
        
        for(var j=0; j<subsamples.length; j++) {
            for(var k in subsamples[j]['avg']) {
                if(subsamples[j]['avg'][k])
                    sample[k].push(subsamples[j]['avg'][k]);
            }

            for(var k in subsamples[j]['sum'])
                sample[k] += subsamples[j]['sum'][k];
        }

        // Sum up arrays of avg values, reduce to number.
        for(var k in subsamples[0]['avg']) {
            var len = sample[k].length;
            var sum = sample[k].reduce(function(a,b){return a+b},0);
            var avg = sum / len;
            sample[k] = avg;
        }

        /*console.log(format('Period #%s, Date=%s, Timespan=[%s to %s], Price=%s',
            (i+1), sample['start'].toLocaleDateString(), sample['start'].toLocaleTimeString(),
            sample['end'].toLocaleTimeString()), sample['price']);
        */
        resampled.push(sample);
    }
    console.log(resampled);
    return resampled;
}

//-----------------------------------------------------------------------------
function get_conf(period) {
    var r = SERIES_CONF.filter(function(elem){if(elem.period.name==period) return elem }, period);
    return r[0];
}

//------------------------------------------------------------------------------
function getTimespan(period, units='ms') {
    /* @period: one of ['1d','7d','1m','3m','6m','1y','ytd','all']
     * @units: result format. 'ms' or 's'
     * Returns: array of ints [t_start, t_end]
    */
    var length = null;
    var today = new Date();
    var end = t_now = today.getTime();

    if(period == 'ytd')
        length = MS_1_DAY * (today.getWeek()*7 + today.getDay());
    else
        length = get_conf(period)['period']['duration'];

    var start = length ? (t_now - length) : null;
    
    return units == 'ms' ? [start, end] : [msToSec(start), msToSec(end)];
}

//------------------------------------------------------------------------------
function fillDataGaps(data) {
    /* Pad any null values in series data w/ prev series value.
    */
    for(var i=0; i<data.length; i++) {
        var p = data[i];
        for(var k in p) {
            if(p[k]) continue;

            for(var j=i; j>=0; j--) {
                if(data[j][k]) {
                    p[k] = data[j][k];
                    break;
                }
            }
            for(var j=i; j<data.length; j++) {
                if(data[j][k]) {
                    p[k] = data[j][k];
                    break;
                }
            }
        }
    }
}

//------------------------------------------------------------------------------
function arrDim(name, arr) {
    if(name == 'min')
        return arr.reduce(function(a,b){ return Math.min(a,b) });
    else if(name == 'max')
        return arr.reduce(function(a,b){ return Math.max(a,b) });
}
