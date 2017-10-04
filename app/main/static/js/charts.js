/* charts.js */

SPIN_DURATION = 3000;
SPIN_ROT_DIST = 360;
MAX_CHART_HT = 500;

prev_wdt = null;
// Rendered morris chart instance
areaChart = null; 
// Div container for morris chart elements
$chartContr = null; 
g_chart_contr_id = null;
g_spin_id = null;
// jCanvas animated chart spinner
$spin = null; 

//-----------------------------------------------------------------------------
function initChart(contr_id, spin_id) {
    /*@contr_id: ID of chart container <div>
     * @spin_id: ID of spinner <canvas>
     */
    g_chart_contr_id = contr_id;
    g_spin_id = spin_id;
    $chartContr = $('#'+contr_id);
    prev_wdt = $chartContr.width();

    // DOM spinner canvas element (DOM coord system)
    var cv = document.getElementById(spin_id);
    cv.width = $chartContr.width();
    cv.height = $chartContr.height();

    // jCanvas spinner object (internal coord system)
    $spin = $('#'+spin_id);
    $spin.width(cv.width);
    $spin.height(cv.height);
    showSpinner(true);
}

//------------------------------------------------------------------------------
function drawChart(data, name, timespan) {
    var series = periodize(data, name, timespan);
    var range = data_range(series);
    var ymin = range['min']; //Number((range['min']-range['spread']/10).toFixed(0));
    showSpinner(false);
    areaChart = Morris.Area({
        element:g_chart_contr_id,
        data:series,
        xkey:'time', ykeys:['price'],
        labels: ['BTC/CAD'],
        ymin:ymin, ymax:range['max'],
        pointSize:0, smooth:false, resize:true
    });
}

//-----------------------------------------------------------------------------
function resizeChart() {
    /* Resize/redraw chart if window/panel has been resized
    */
    if(!areaChart || !$chartContr || $chartContr.width()==prev_wdt)
        return;
    if($chartContr.height() > MAX_CHART_HT)
        $chartContr.height(MAX_CHART_HT);
    prev_wdt = $chartContr.width();

    // Resize canvas coordinate dimensions
    var cv = document.getElementById(g_spin_id);
    cv.width = prev_wdt

    // Resize jCanvas DOM dimensions
    $spin.width(cv.width);
    $spin.height(cv.height);
    // Adjust jCanvas layer positions
    var layers = $spin.getLayers();
    for(var i=0; i<layers.length; i++) {
        var layer = layers[i];
        layer.x = cv.width/2 - layer.width/2;
        if(layer.name == 'title')
            continue;
    }
    $spin.drawLayers();

    $('svg').height(MAX_CHART_HT - 50);
    $('svg').width($chartContr.width());
    areaChart.redraw();
    $('#side_frm').height($('#main_frm').height());
   
    console.log('resizing chart, w='+$chartContr.width()+', h='+$chartContr.height());
}

//------------------------------------------------------------------------------
function showSpinner(show) {
    /* Rotating star spinner displayed while charts are loading.
    */
    if(!$spin)
        return;
    if(!$spin.getLayer('loader')) {
        var cv = document.getElementById(g_spin_id);
        // Initial drawing.
        $spin.drawPolygon({
            layer:true, name:'loader', fillStyle:'rgba(39, 155, 190, 0.5)',
            x:cv.width/2, y:cv.height/2, radius:50, sides:5, concavity:0.5
        });
    }
    if(show) {
        $chartContr.find('svg').remove();
        $chartContr.find('.morris-hover').remove();

        $spin.getLayer('loader').visible = true;
        $spin.show();
        rotateSpinner();
    }
    else {
        $spin.getLayer('loader').visible = false;
        $spin.hide();
    }
}

//------------------------------------------------------------------------------
function rotateSpinner() {
    SPIN_ROT_DIST *= -1;
    $spin.animateLayer(
        'loader',
        { rotate:SPIN_ROT_DIST },
        SPIN_DURATION,
        rotateSpinner
    );
}
