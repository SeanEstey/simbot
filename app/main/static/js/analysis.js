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
    var mktChrt = new Chart('mkt-cont', 'Area');
    mktChrt.toggleSpinner(true);
    mktChrt.addSeries('/trades/get',
      {ex:'QuadrigaCX', asset:'btc', label:'price', ykey:'price', type:'area', decimals:2, time_lbl:'1d'});

    var orderBookCharts = new Chart('ord-chrt-contr', 'Area');
    orderBookCharts.toggleSpinner(true);
    orderBookCharts.addSeries(
      '/indicators/book',
      {ex:'QuadrigaCX', asset:'btc', label:'v_ask', ykey:'v_ask', type:'line', decimals:3, time_lbl:'1d'}
    );
    orderBookCharts.addSeries(
      '/indicators/book',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bid', ykey:'v_bid', type:'line', decimals:3, time_lbl:'1d'}
    );

    var buyChrt = new Chart('buy_rate-cont', 'Area');
    buyChrt.toggleSpinner(true);
    buyChrt.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'buy_rate', ykey:'buy_rate', type:'area', decimals:2, time_lbl:'1d'}
    );

    var orders2Chart = new Chart('orders2-cont', 'Area');
    orders2Chart.toggleSpinner(true);
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid', ykey:'bid', type:'area', decimals:2, time_lbl:'1d'}
    );
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask', ykey:'ask', type:'area', decimals:2, time_lbl:'1d'}
    );
    var orders3Chart = new Chart('orders3-cont', 'Area');
    orders3Chart.toggleSpinner(true);
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );



    var orders5Chart = new Chart('orders5-cont', 'Area');
    orders5Chart.toggleSpinner(true);
    orders5Chart.addSeries(
      '/indicators/trade',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bought', ykey:'v_bought', type:'line', decimals:2, time_lbl:'1d'}
    );
    orders5Chart.addSeries(
      '/indicators/trade',
      {ex:'QuadrigaCX', asset:'btc', label:'v_sold', ykey:'v_sold', type:'line', decimals:2, time_lbl:'1d'}
    );


    $(window).resize(function(){
        mkrChrt.resize();
        orderBookCharts.resize();
        orders2Chart.resize();
        orders3Chart.resize();
        orders4Chart.resize();
        orders5Chart.resize();
    })
}
