/* charts.js */
MS_10_MIN = 600000;
//MS_1_HR = 3600000;
MS_1_DAY = 86400000;
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

//-----------------------------------------------------------------------------
function Chart(contId, type) {
    /* Morris.js chart supporting multi-series data, capable of dynamically
     * modifying series and redrawing.
     */
    this.MaxHeight = 400;
    this.SpinCycleDegrees = 360;
    this.SpinDuration = 3000;
    this.morrisObj = null;
    this.series = [];
    this.type = type;
    this.contId = contId;
    this.$cont = $('#'+this.contId);
    // DOM spinner canvas element (DOM coord system)
    this.spinnerId = contId + '-spinner';
    this.$cont.find('canvas').prop('id', this.spinnerId);
    this.cv = document.getElementById(this.spinnerId);
    this.cv.width = this.$cont.width();
    this.cv.height = this.$cont.height();
    // jCanvas spinner object (internal coord system)
    this.$spinner = $('#'+this.spinnerId);
    this.$spinner.width(this.cv.width);
    this.$spinner.height(this.cv.height);
    this.prevWidth = this.$cont.width();

    this.toggleSpinner(true);
    //$(window).resize(function(){this.resize()});
}

Chart.prototype.querySeries = function(url, options) {
    this.querySeriesData(url, options, this.series.length+1);
}

Chart.prototype.addSeries = function(data, options) {
    var _options = JSON.parse(JSON.stringify(options));
    _options['data'] = data;
    this.series.push(_options);
    this.draw();
}

Chart.prototype.replaceSeries = function(url, options, idx) { 
    this.querySeriesData(url, options, idx); 
}

Chart.prototype.rmvSeries = function(idx) {
    this.series.splice(idx,1);
    this.draw();
}

//------------------------------------------------------------------------------
Chart.prototype.combineSeries = function() {
    /* Build 1D array for rendering chart.
    */
    if(this.series.length < 1)
        return;

    var data = [];

    // Create datapoints by combining series data for each time period.
    for(var i=0; i<this.series[0]['data'].length; i++) { 
        var point = { 'time':this.series[0]['data'][i]['date'] };

        for(var j=0; j<this.series.length; j++) {
            var s = this.series[j];
            point[s['label']] = s['data'][i][s['ykey']];
        }
        data.push(point);
    }
    this.fillDataGaps(data);
    //console.log(data);
    return data;
}

//------------------------------------------------------------------------------
Chart.prototype.getSeriesIdx = function(series_lbl=false, selected_by=false) {
    var k = v = null;
    if(typeof series_lbl !== 'undefined') {
        k = 'label';
        v = series_lbl;
    }
    else if(typeof selected_by !== 'undefined') {
        k = 'selected_by';
        v = selected_by;
    }
    for(var idx=0; idx<this.series.length; idx++) {
        if(this.series[idx][k] == v) return idx;
    }
    return -1;
}

//------------------------------------------------------------------------------
Chart.prototype.querySeriesData = function(url, options, idx) {
    /* POST request returning series data  */
    var data = null;
    var tspan = getTimespan(options['time_lbl'], units='s');
    $.ajax({
        type: 'POST',
        url: BASE_URL + url,
        data:{
            ex:options['ex'],
            asset:options['asset'],
            ykey:options['ykey'],
            since:tspan[0] + (3600*6), // convert to UTC
            until:tspan[1] + (3600*6) // convert to UTC
        },
        async:true,
        context: this,
        success:function(json){ 
            var data = JSON.parse(json);
            var _options = JSON.parse(JSON.stringify(options));
            _options['data'] = data;
            if(idx > this.series.length)
                this.series.push(_options);
            else
                this.series[idx] = _options;
            this.draw();
        }
    });
}

//------------------------------------------------------------------------------
Chart.prototype.yValueAvg = function(data, k, start, end) {
    /* Timeseries average y-val.
    */
    var y_values = data.filter(
        function(elem, j, data) {
            var d = elem['date']['$date'];
            if(d >= start && d < end) return elem;
        }
    ).map(function(x) { return x[k] });

    if(y_values.length == 0)
        return null;
    else
        return Number((y_values.reduce(function(a,b){ return a+b }) / y_values.length)) 
}

//------------------------------------------------------------------------------
Chart.prototype.fillDataGaps = function(data) {
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

//-----------------------------------------------------------------------------
Chart.prototype.resize = function() {
    /* Resize/redraw chart if window/panel has been resized
    */
    if(!this.morrisObj || !this.$cont || this.$cont.width()==this.prevWidth)
        return;
    if(this.$cont.height() > this.MaxHeight)
        this.$cont.height(this.MaxHeight);
    this.prevWidth = this.$cont.width();
    // Resize canvas coordinate dimensions
    this.cv.width = this.prevWidth;
    // Resize jCanvas DOM dimensions
    this.$spinner.width(this.cv.width);
    this.$spinner.height(this.cv.height);
    // Adjust jCanvas layer positions
    var layers = this.$spinner.getLayers();
    for(var i=0; i<layers.length; i++) {
        var layer = layers[i];
        layer.x = this.cv.width/2 - layer.width/2;
    }
    this.$spinner.drawLayers();
    this.$cont.find('svg').height(this.MaxHeight - 50);
    this.$cont.find('svg').width(this.$cont.width());
}

//------------------------------------------------------------------------------
Chart.prototype.draw = function() {
    /* Draw chart from series data.
    */
    this.erase();
    this.toggleSpinner(false);
    var options = {
        element: this.contId,
        data: this.combineSeries(),
        xkey: 'time',
        ykeys: this.series.map(function(x){return x.label}),
        labels: this.series.map(function(x){return x.label}),
        yLabelFormat: function(y) {return y = Number(y.toFixed(2))},
        ymin: 'auto',
        ymax: 'auto',
        smooth: false,
        pointSize: 0,
        pointStrokeColors: ['black'],
        pointFillColors: ['white'],
        lineColors: ['#5cb85c','red', '#136d8d', 'pink'],
        fillOpacity: 0.3,
        dateFormat: function(x) { return new Date(x).toLocaleString()},
        hideHover: 'auto',
        //hideHover: 'always',
        //preUnits: '$',
        behaveLikeLine: true,
        resize: true
    };

    if(this.type == 'line')
        this.morrisObj = Morris.Line(options);
    else if(this.type == 'area')
        this.morrisObj = Morris.Area(options);

    //this.resize();
}

//------------------------------------------------------------------------------
Chart.prototype.erase = function() {
    this.$cont.find('svg').remove();
    this.$cont.find('.morris-hover').remove();
    this.morrisObj = null;
}

//------------------------------------------------------------------------------
Chart.prototype.toggleSpinner = function(bShow) {
    /* Rotating star spinner displayed while charts are loading.
    */
    if(!this.$spinner)
        return;

    if(!this.$spinner.getLayer('loader')) {
        // Initial drawing.
        this.$spinner.drawPolygon({
            layer:true, name:'loader', fillStyle:'rgba(39, 155, 190, 0.5)',
            x:this.cv.width/2, y:this.cv.height/2, radius:50, sides:5, concavity:0.5
        });
        this.$spinner.drawLayers();
    }

    if(bShow) {
        this.erase();
        this.$cont.find('svg').remove();
        this.$cont.find('.morris-hover').remove();
        this.$spinner.getLayer('loader').visible = true;
        this.$spinner.show();
        this.rotateSpinner();
    }
    else {
        this.$spinner.getLayer('loader').visible = false;
        this.$spinner.hide();
    }
}

//------------------------------------------------------------------------------
Chart.prototype.rotateSpinner = function() {
    if(this instanceof Chart) {
        this.SpinCycleDegrees *= -1;
        this.$spinner.animateLayer(
            'loader',
            { rotate:this.SpinCycleDegrees },
            this.SpinDuration,
            this.rotateSpinner
        );
    }
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
