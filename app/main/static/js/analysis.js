/* analysis.js */
BASE_URL = "http://45.79.176.125";
TIME_LBL = '7d';

//------------------------------------------------------------------------------
function initMain() {
    initSlidePanel('markets');
    initSlidePanel('orders');
    initSlidePanel('orders2');

    showOrderBookCharts();
}

//------------------------------------------------------------------------------
function showOrderBookCharts() {
    var market = new Chart('mkt-cont', 'Area');
    var v_orders = new Chart('ord-chrt-contr', 'Area');
    var books = new Chart('orders2-cont', 'Area');
    var inertia = new Chart('orders3-cont', 'Area');

    var trade1 = new Chart('trade1-cont', 'Area');
    var trade2 = new Chart('trade2-cont', 'Area');

    var tspan = market.getTimespan(TIME_LBL, units='s');
    $.ajax({
        type: 'POST',
        url: BASE_URL + '/indicators/get',
        data:{
            ex:'QuadrigaCX',
            asset:'btc',
            since:tspan[0] + (3600*6), // convert to UTC
            until:tspan[1] + (3600*6) // convert to UTC
        },
        async:true,
        context: this,
        success:function(json){ 
            var raw = JSON.parse(json);
            var resample_data = market.resample(TIME_LBL, raw);

            market.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'price', ykey:'price', type:'area',
                decimals:2, time_lbl:TIME_LBL});
            v_orders.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_vol', ykey:'ask_vol', type:'line',
                decimals:3, time_lbl:TIME_LBL});
            v_orders.addSeries(resample_data, 
                {ex:'QuadrigaCX', asset:'btc', label:'bid_vol', ykey:'bid_vol', type:'line',
                decimals:3, time_lbl:TIME_LBL});

            trade1.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'area',
                decimals:3, time_lbl:TIME_LBL});
            trade1.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'buy_vol', ykey:'buy_vol', type:'area',
                decimals:2, time_lbl:TIME_LBL});

            trade2.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'area',
                decimals:3, time_lbl:TIME_LBL});
            trade2.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'sell_vol', ykey:'sell_vol', type:'area',
                decimals:2, time_lbl:TIME_LBL});

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

            books.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'bid_price', ykey:'bid_price', type:'line',
                decimals:2, time_lbl:TIME_LBL});
            books.addSeries(resample_data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_price', ykey:'ask_price', type:'line',
                decimals:2, time_lbl:TIME_LBL});
        }
    });
}
