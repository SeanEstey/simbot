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
    orderBookCharts = new Chart('ord-chrt-contr', 'Area');
    orderBookCharts.toggleSpinner(true);
    orderBookCharts.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'v_ask', ykey:'v_ask', type:'line', decimals:3, time_lbl:'1d'}
    );
    orderBookCharts.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bid', ykey:'v_bid', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders2Chart = new Chart('orders2-cont', 'Area');
    orders2Chart.toggleSpinner(true);
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid', ykey:'bid', type:'area', decimals:2, time_lbl:'1d'}
    );
    orders2Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask', ykey:'ask', type:'area', decimals:2, time_lbl:'1d'}
    );
    orders3Chart = new Chart('orders3-cont', 'Area');
    orders3Chart.toggleSpinner(true);
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders3Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'line', decimals:3, time_lbl:'1d'}
    );
    orders4Chart = new Chart('orders4-cont', 'Area');
    orders4Chart.toggleSpinner(true);
    orders4Chart.addSeries(
      '/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'buy_rate', ykey:'buy_rate', type:'area', decimals:2, time_lbl:'1d'}
    );
    $(window).resize(function(){
        orderBookCharts.resize();
        orders2Chart.resize();
        orders3Chart.resize();
        orders4Chart.resize();
    })
}
