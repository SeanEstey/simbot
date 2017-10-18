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

    market.addSeries('/trades/get',
      {ex:'QuadrigaCX', asset:'btc', label:'price', ykey:'price', type:'area', decimals:2, time_lbl:'7d'});
    v_orders.addSeries('/indicators/book',
      {ex:'QuadrigaCX', asset:'btc', label:'v_ask', ykey:'v_ask', type:'line', decimals:3, time_lbl:'7d'}
    );
    v_orders.addSeries('/indicators/book',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bid', ykey:'v_bid', type:'line', decimals:3, time_lbl:'7d'}
    );
    buy_rate.addSeries('/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'buy_rate', ykey:'buy_rate', type:'area', decimals:2, time_lbl:'7d'}
    );
    inertia.addSeries('/indicators/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid_inertia', ykey:'bid_inertia', type:'line', decimals:3, time_lbl:'7d'}
    );
    inertia.addSeries('/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask_inertia', ykey:'ask_inertia', type:'line', decimals:3, time_lbl:'7d'}
    );
    v_traded.addSeries('/indicators/trade',
      {ex:'QuadrigaCX', asset:'btc', label:'v_bought', ykey:'v_bought', type:'line', decimals:2, time_lbl:'7d'}
    );
    v_traded.addSeries('/indicators/trade',
      {ex:'QuadrigaCX', asset:'btc', label:'v_sold', ykey:'v_sold', type:'line', decimals:2, time_lbl:'7d'}
    );
    /*books.addSeries('/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'bid', ykey:'bid', type:'area', decimals:2, time_lbl:'7d'}
    );
    books.addSeries('/books/get',
      {ex:'QuadrigaCX', asset:'btc', label:'ask', ykey:'ask', type:'area', decimals:2, time_lbl:'7d'}
    );*/
}
