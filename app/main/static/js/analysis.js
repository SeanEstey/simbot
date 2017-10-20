/* analysis.js */
BASE_URL = "http://45.79.176.125";

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
    var buy_rate = new Chart('buy_rate-cont', 'Area');
    var books = new Chart('orders2-cont', 'Area');
    var inertia = new Chart('orders3-cont', 'Area');
    var v_traded = new Chart('orders5-cont', 'Area');

    var data = null;
    var tspan = market.getTimespan('7d', units='s');
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
            var data = JSON.parse(json);
            for(var i=0; i<data.length; i++) {
                data[i]['date'] = data[i]['start'];
                for(var k in data[i]['avg']) {
                    data[i][k] = data[i]['avg'][k];
                }
                for(var k in data[i]['sum']) {
                    data[i][k] = data[i]['sum'][k];
                }
            }
            //console.log(data);
            market.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'price', ykey:'price', type:'area',
                decimals:2, time_lbl:'1d'});
            v_orders.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_vol', ykey:'ask_vol', type:'line',
                decimals:3, time_lbl:'7d'});
            v_orders.addSeries(data, 
                {ex:'QuadrigaCX', asset:'btc', label:'bid_vol', ykey:'bid_vol', type:'line',
                decimals:3, time_lbl:'7d'});
            inertia.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'line',
                decimals:3, time_lbl:'7d'});
            inertia.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'line',
                decimals:3, time_lbl:'7d'});
            v_traded.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'buy_vol', ykey:'buy_vol', type:'line',
                decimals:2, time_lbl:'7d'});
            v_traded.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'sell_vol', ykey:'sell_vol', type:'line',
                decimals:2, time_lbl:'7d'});
            books.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'bid_price', ykey:'bid_price', type:'area',
                decimals:2, time_lbl:'7d'});
            books.addSeries(data,
                {ex:'QuadrigaCX', asset:'btc', label:'ask_price', ykey:'ask_price', type:'area',
                decimals:2, time_lbl:'7d'});
            //buy_rate.addSeries(data, {ex:'QuadrigaCX', asset:'btc', label:'buy_rate', ykey:'buy_rate',
                type:'area', decimals:2, time_lbl:'7d'});
        }
    });
}
