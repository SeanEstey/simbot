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
graph = null;
BASE_URL = "http://45.79.176.125";
ticksTreatment = 'glow';
periodLabel = '1d';
exchange = 'QuadrigaCX';
asset = 'btc';
pair = ['btc','cad'];
seriesData = [
    {name:'Bids', renderer:'line', color:'red', data:[]},
    {name:'Asks', renderer:'line', color:'green', data:[]},
    {name:'Trades', renderer:'line', color:'steelblue', data:[]}
];

//------------------------------------------------------------------------------
function initMain() {
    initGraph();
    initSocketIO();
}

//------------------------------------------------------------------------------
function onUpdateGraphStream(response) {
    var response = JSON.parse(response);
    var data = response['data'];

    if(data['ex'] != exchange || data['pair'].join("_") != pair.join("_"))
        return;

    console.log(response);

    if(response['type'] == 'orderbook') {
        var vtot = seriesData[2]['data'][seriesData[2]['data'].length-1]['x'];

        // Graph Asks
        var vask = vtot;
        seriesData[1]['data'] = data['asks'].map(function(n){
            vask+=n[1]; 
            return { x:vask, y:n[0] };
        });

        // Graph Bids
        var vbid = vtot;
        seriesData[0]['data'] = data['bids'].map(function(n){
            vbid += n[1];
            return { x:vbid, y:n[0] };
        });
        var spliceIdx=0;
        for(var i=0; i<seriesData[0]['data'].length; i++) {
            var vol = seriesData[0]['data'][i]['x'];
            if(vol - vtot > 75) {
                spliceIdx=i;
                break;
            }
        }
        if(spliceIdx > 0) {
            var len = seriesData[0]['data'].length;
            seriesData[0]['data'].splice(spliceIdx, len-1);
        }
    }
    else if(response['type'] == 'trade') {
        var len = seriesData[2]['data'].length;
        var v_tot = 0;
        if(len > 0)
            v_tot = seriesData[2]['data'][len-1]['x'];
        //if(len > 100)
        //    seriesData[2]['data'].splice(0,1);
        seriesData[2]['data'].push({
            x:Number(v_tot + Number(data['amount'])),
            y:Number(data['price'])
        });
    }

    graph.update();
}

//------------------------------------------------------------------------------
function onInitGraphStream(response) {
    var data = JSON.parse(response);
    console.log(data);
    var v_total = 0;
    seriesData[2]['data'] = data.map(function(n) {
        v_total += n['volume'];
        return {x:v_total, y:Number(n['price'])}
    });
    graph.update();
}

//------------------------------------------------------------------------------
function initSocketIO() {
    socket = io.connect(BASE_URL);
    socket.on('connect', function(){
        console.log('socket.io connected!');
        socket.emit('initGraphStream');
    });

    socket.on('initGraphStream', onInitGraphStream);
    socket.on('updateGraphStream', onUpdateGraphStream);
}

//------------------------------------------------------------------------------
function initGraph() {
    var palette = new Rickshaw.Color.Palette( { scheme: 'classic1' } );
    graph = new Rickshaw.Graph( {
        element: getElemById("chart"),
        height: 500,
        renderer: 'line',
        interpolation:'linear',
        min:'auto',
        //stroke: true,
        //preserve: true,
        series: seriesData 
    } );
    graph.render();

    var legend = new Legend(
        {graph:graph, element:getElemById('legend')});
    var toggle = new SeriesToggle(
        {graph:graph, legend:legend});
    var order = new Order(
        {graph:graph, legend:legend});
    var highlighter = Highlight(
        {graph:graph, legend:legend});
    var hoverDetail = new Rickshaw.Graph.HoverDetail(
        {graph:graph, xFormatter:function(x) {return new Date(x*1000).toString();}});
    var xAxis = new Rickshaw.Graph.Axis.X(
        {graph:graph});
    xAxis.render();
    var yAxis = new Rickshaw.Graph.Axis.Y({
        graph:graph, orientation:'left', tickFormat:Rickshaw.Fixtures.Number.formatKMBT,
        element:getElemById('y_axis')
    });
    yAxis.render();
    //var annotator = new Annotate(
    //    {graph:graph, element:getElemById('timeline')});
    //addAnnotations(annotator, random);
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
