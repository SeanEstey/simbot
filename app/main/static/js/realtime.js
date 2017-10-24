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
BASE_URL = "http://45.79.176.125";
graph = null;
periodLabel = '1d';
exchange = 'QuadrigaCX';
asset = 'btc';
ticksTreatment = 'glow';
seriesData = [];

//------------------------------------------------------------------------------
function initMain() {
    initSocketIO();

    $.ajax({
        type: 'POST',
        url: BASE_URL + '/indicators/get',
        data:{
            ex:exchange,
            asset:asset,
            since:getTimespan(periodLabel, units='s')[0] + (3600*6), // convert to UTC
            until:getTimespan(periodLabel, units='s')[1] + (3600*6)
        },
        async:true,
        context: this,
        success:function(json){
            var raw = JSON.parse(json);
            var resampled = resampleData('1d', raw);
            seriesData = resampled.map(function(elem) {
                return {x:elem['date']/1000, y:elem['price']}
            });
            fillDataGaps(seriesData);
            renderChart(seriesData);
        }
    });
}

//------------------------------------------------------------------------------
function initSocketIO() {
    socket = io.connect(BASE_URL);
    socket.on('connect', function(){
        console.log('socket.io connected!');
    });
    socket.on('newTrade', function(data){
        if(data['pair'].join("_") != "btc_cad")
            return;

        seriesData.splice(0,1);
        var d = {x:Number(data['date']), y:Number(data['price'])};
        seriesData.push(d);
        graph.update();
        console.log('updating graph w/ new trade');
    });
}

//------------------------------------------------------------------------------
function renderChart(data) {
    var palette = new Rickshaw.Color.Palette( { scheme: 'classic1' } );
    var graph = new Rickshaw.Graph( {
        element: getElemById("chart"),
        //width: 900,
        height: 500,
        renderer: 'area',
        min:'auto',
        stroke: true,
        preserve: true,
        series: [
            {color:'steelblue', data:data, name:'QuadrigaCX'}
        ]
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
    var xAxis = new Rickshaw.Graph.Axis.Time(
        {graph:graph}); //, ticksTreatment:ticksTreatment, timeFixture:new Rickshaw.Fixtures.Time.Local()});
    xAxis.render();
    var yAxis = new Rickshaw.Graph.Axis.Y(
        {graph:graph, tickFormat:Rickshaw.Fixtures.Number.formatKMBT});
    yAxis.render();

    //var annotator = new Annotate(
    //    {graph:graph, element:getElemById('timeline')});
    //addAnnotations(annotator, random);
}

function getElemById(_id){ return document.getElementById(_id); }
function querySelector(name){ return document.querySelector(name); }

//------------------------------------------------------------------------------
function addAnnotations(annotator, random) {
    var messages = [
        "Changed home page welcome message",
        "Minified JS and CSS",
        "Changed button color from blue to green",
        "Refactored SQL query to use indexed columns",
        "Added additional logging for debugging",
        "Fixed typo",
        "Rewrite conditional logic for clarity",
        "Added documentation for new methods"
    ];

    setInterval( function() {
        random.removeData(seriesData);
        random.addData(seriesData);
        graph.update();
    }, 3000);

    function addAnnotation(force) {
        if (messages.length > 0 && (force || Math.random() >= 0.95)) {
            annotator.add(seriesData[2][seriesData[2].length-1].x, messages.shift());
            annotator.update();
        }
    }
    addAnnotation(true);
    setTimeout( function() { setInterval( addAnnotation, 6000 ) }, 6000 );
}

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
