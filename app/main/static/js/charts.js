/* charts.js */

morris = null; // morris.js app
areaChart = null; // area chart instance
chart_id = null;
last_chart_width = null;
$chart = null; 
placehld_id = null;
$placehld = null; // jCanvas chart loader
t1 = new Date();
angle = 360;

//-----------------------------------------------------------------------------
function initChart(elem_id, loader_id) {
    /* @elem_id: chart parent div id
    @loader_id: child canvas selector id
    */
    chart_id = elem_id;
    $chart = $('#'+chart_id);
    last_chart_width = $chart.width();
    console.log($chart.width());

    // Make canvas coord dimensions match DOM dimensions
    placehld_id = loader_id;
    // Html canvas
    var placehld_cv = document.getElementById(loader_id);
    placehld_cv.width = $chart.width();
    placehld_cv.height = $chart.height();
    // jCanvas
    $placehld = $('#'+placehld_id);
    $placehld.width(placehld_cv.width);
    $placehld.height(placehld_cv.height);
    $placehld.drawPolygon({
      layer:true,
      name:'loader',
      fillStyle:'rgba(39, 155, 190, 0.5)',
      x:placehld_cv.width/2,
      y:placehld_cv.height/2,
      radius: 50,
      sides: 5,
      concavity: 0.5
    });
    $placehld.getLayer('loader').visible = true;

    // Event handlers
    $(window).resize(function(e) {
        if($chart.width() != last_chart_width)
            resizeCanvas();
    });
}

//------------------------------------------------------------------------------
function showLoader() {
    //$('#chart-panel').collapse('show');
    //$chart.find('svg').remove();
    //$chart.find('.morris-hover').remove();
    $placehld.getLayer('loader').visible = true;
    $placehld.show();
    loopLoaderAnim();
}

//------------------------------------------------------------------------------
function hideLoader() {
    $placehld.getLayer('loader').visible = false;
    $placehld.hide();
    //$chart.find('svg').show();
}

//------------------------------------------------------------------------------
function avgPrice(data, start, end) {
    /* Price average within time period */
    var in_period = data.filter(function(elem, j, data) {
        var d = elem['date']['$date'];

        if(d >= start && d < end)
            return elem['price'];
    });

    var p = in_period.map(function(x){ return x.price });

    if(p.length == 0)
        return -1;

    var avg = p.reduce(function(a,b){ return a+b }) / p.length;
    return Number(avg.toFixed(0));
}

//------------------------------------------------------------------------------
function lastPrice(series, idx) {
    for(var i=idx; i>=0; i--) {
        if(series[i]['price'] > 0)
            return series[i]['price'];
    }
    return -1;
}

//------------------------------------------------------------------------------
function drawAreaChart(data) {
    hideLoader();

    // Divide x-axis into 10 min segments, averaging price for each.
    var series = [];
    var t_first = new Date(new Date().getTime() - (1000*3600*24)).getTime();
    var p_duration = 1000*60*10;
    var n_periods = 24*6;

    for(var i=0; i<n_periods; i++) {
        var t_start = t_first + (i*p_duration);
        var avg = avgPrice(data, t_start, t_start+p_duration);
        series.push({ price:avg, time:t_start });
    }

    for(var i=0; i<series.length; i++) {
        if(series[i]['price'] == -1)
            series[i]['price'] = lastPrice(series,i);
    }

    var prices = data.map(function(x){ return x.price});
    var min = Number(Math.min.apply(null,prices).toFixed(0));
    var max = Number(Math.max.apply(null,prices).toFixed(0));
    var spread = max - min;

    areaChart = Morris.Area({
      element: 'chart',
      data: series,
      xkey: 'time',
      ykeys: ['price'],
      ymax: max,
      ymin: min - spread/10,
      pointSize: 0,
      smooth: false,
      labels: ['BTC/CAD'],
      resize:true
    });
}

//------------------------------------------------------------------------------
function displayError(msg, response) {
    $('#main').prop('hidden', true);
    $('#error').prop('hidden', false);
    $('#err_alert').prop('hidden', false);
    alertMsg(msg, 'danger', id="err_alert");
}

//-----------------------------------------------------------------------------
function loopLoaderAnim(){
    var loopDuration = 3000;
    angle = angle *-1;
    var p = $placehld.getLayer('loader');
    $placehld.animateLayer(
        'loader',
        {rotate:angle},
        loopDuration,
        loopLoaderAnim
    );
}

//-----------------------------------------------------------------------------
function resizeCanvas() {
    if($chart.height() > 450*.75)
        $chart.height(450*.75);

    last_chart_width = $chart.width();

    // Resize canvas coordinate dimensions
    var placehld_cv = document.getElementById(placehld_id);
    placehld_cv.width = last_chart_width;

    // Resize DOM canvas dimensions
    $placehld.width(placehld_cv.width);
    $placehld.height(placehld_cv.height);

    // Adjust layer positions
    var layers = $placehld.getLayers();
    for(var i=0; i<layers.length; i++) {
        var layer = layers[i];
        layer.x = placehld_cv.width/2 - layer.width/2;
        if(layer.name == 'title')
            continue;
    }
    $placehld.drawLayers();
    $('svg').width($chart.width());

    console.log('resizeCanvas. chart w='+$chart.width()+', h='+$chart.height());
    areaChart.redraw();
}
