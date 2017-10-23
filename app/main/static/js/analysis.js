/* analysis.js */
BASE_URL = "http://45.79.176.125";
TIME_LBL = '7d';
EX = 'QuadrigaCX';

priceChart = null; 
ordBookChart = null;
buyVolChart = null;
sellVolChart = null;

//------------------------------------------------------------------------------
function initMain() {
    initCharts();
    generateGroupCharts('QuadrigaCX', 'btc', '1d');
    initEventHandlers();
}

//------------------------------------------------------------------------------
function initCharts() {
    initSlidePanel('prices');
    initSlidePanel('orders');
    initSlidePanel('trade1');
    initSlidePanel('trade2');

    priceChart = new Chart('mkt-cont', 'area');
    ordBookChart= new Chart('ordbook-cont', 'line');
    buyVolChart = new Chart('trade1-cont', 'area');
    sellVolChart = new Chart('trade2-cont', 'area');
}

//------------------------------------------------------------------------------
function initEventHandlers() {

    // Exchange changed.
    $('#controls input[type="checkbox"]').change(function() {
        var time_lbl = $('#controls select[name="time_lbl"]').val();
        var asset = $('#controls select[name="asset"]').val();
        var series_lbl = $(this).prop('name');

        if($(this)[0].checked) {
            marketChart.toggleSpinner(true);
            marketChart.addSeries(
              '/trades/get',
              {ex:series_lbl, asset:asset, label:series_lbl, ykey:'price', type:'area', decimals:2, time_lbl:time_lbl}
            );
        }
        else if(!$(this)[0].checked) {
            marketChart.toggleSpinner(true);
            var idx = marketChart.getSeriesIdx(series_lbl);
            marketChart.rmvSeries(idx);
        }
    });

    // Asset/period name changed.
    $('#controls select').change(function(){
        var period = $('#controls select[name="time_lbl"]').val();
        var asset = $('#controls select[name="asset"]').val();
        initCharts();
        generateGroupCharts(EX, asset, period);
    });
}

//------------------------------------------------------------------------------
function generateGroupCharts(ex, asset, period) {

    console.log(format('Generating charts, ex=%s, asset=%s, period=%s',
        ex, asset, period));

    var tspan = getTimespan(period, units='s');

    $.ajax({
        type: 'POST',
        url: BASE_URL + '/indicators/get',
        data:{
            ex:ex,
            asset:asset,
            since:tspan[0] + (3600*6), // convert to UTC
            until:tspan[1] + (3600*6) // convert to UTC
        },
        success:function(json){ 
            var raw = JSON.parse(json);
            var rsdata = resampleData(period, raw);

            priceChart.addSeries(rsdata, {label:'price', ykey:'price', decimals:2});

            ordBookChart.addSeries(rsdata, {label:'ask_vol', ykey:'ask_vol', decimals:3});
            ordBookChart.addSeries(rsdata, {label:'bid_vol', ykey:'bid_vol', decimals:3});

            buyVolChart.addSeries(rsdata, {label:'ask_inertia', ykey:'ask_inertia', decimals:3});
            buyVolChart.addSeries(rsdata, {label:'buy_vol', ykey:'buy_vol', decimals:2});

            sellVolChart.addSeries(rsdata, {label:'bid_inertia', ykey:'bid_inertia', decimals:3});
            sellVolChart.addSeries(rsdata, {label:'sell_vol', ykey:'sell_vol', decimals:2});
        }
    });

}

//------------------------------------------------------------------------------
/* Annotate area where vol > intertia:
    // Highlight vertex
    <circle
        cx="720.1004601903709" cy="213.9199054798183"
        r="5" fill="blue" stroke="blue" stroke-width="5"
        style="-webkit-tap-highlight-color: rgba(0, 0, 0, 0);">
    </circle>

    // Add text annotation
    <text
        x="628.4920264554312" y="212.55307205502413"
        text-anchor="middle" font="10px &quot;Arial&quot;" stroke="none" fill="red"
        style="-webkit-tap-highlight-color: red; text-anchor: middle; font-style: normal; font-variant: normal; font-weight: normal; font-stretch: normal; font-size: 12px; line-height: normal; font-family: sans-serif;"
        font-size="12px" font-family="sans-serif" font-weight="normal" transform="matrix(1,0,0,1,0,6.6641)">
        <tspan style="-webkit-tap-highlight-color: rgba(0, 0, 0, 0);" dy="4.00262451171875">
             ASK INERTIA CRITICAL!
        </tspan>
    </text>
*/
