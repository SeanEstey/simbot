# app.main.endpoints
from datetime import datetime, timedelta
from bson.json_util import dumps
import logging, pprint
from flask import g, request

log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare
from .simulate import SimBot
from .indicators import get_book_metrics

@main.route('/stats/get', methods=['POST'])
def get_earnings():
    gary = SimBot('Terry')
    return dumps(gary.stats())

@main.route('/holdings/get', methods=['POST'])
def get_holdings():
    gary = SimBot('Terry')
    holdings = gary.holdings()
    return dumps(holdings)

@main.route('/tickers/get', methods=['POST'])
def get_tickers():
    tickers = list(g.db['exchanges'].find())
    return dumps(tickers)

@main.route('/trades/get', methods=['POST'])
def get_trades():
    get = request.form.get
    trades = list(
        g.db['pub_trades'].find({
            'exchange':get('ex'),
            'currency':get('asset'),
            'date':{'$gte':datetime.fromtimestamp(int(get('since')))}
        }).sort('date',1)
    )
    return dumps(trades)

@main.route('/books/get', methods=['POST'])
def _get_books():
    get = request.form.get
    return get_book_metrics(
        get('ex'),
        '%s_cad' % get('asset'),
        get('ykey'),
        datetime.fromtimestamp(int(get('since'))),
        datetime.fromtimestamp(int(get('until')))
    )

@main.route('/books/update', methods=['POST'])
def _update_books():
    exchange = request.form.get('exchange')
    if exchange == 'Coinsquare':
        coinsquare.update('CAD', 'BTC')
    return 'OK'

@main.route('/books/indicators', methods=['POST'])
def _indicators():
    """Return time-series for order book and trade
    indicators for rendering to chart.

    # Run aggregate query for pub_books
    book_analysis = g.db['pub_books'].aggregate([
        {'$group':
            {'_id':'$ex', 'book':'$book', 'bids':
            'v_bid':{'$sum':'$bids.$1'}
        'v_ask':{'$sum':'$asks.$1'}
        'v_ratio':round(v_bid/v_ask,2),
        'p_ask_sens':{'$min':..
        ])

    trade_analysis = g.db['pub_trades'].aggregate([
        'n_sell_mkt_orders':n_sell,
        'n_buy_mkt_orders':n_buy,
        'buy_ratio': round(n_buy/(n_buy+n_sell),2)

            {'$group':{'_id':'$book', 'name':'$ex', 'min_ask':{'$min':'$ask'}, 'max_bid':{'$max':'$bid'}}}])
    ])
    """

    return dumps([
        list(g.db['pub_books'].find(
            {'ex':'QuadrigaCX', 'book':'btc_cad'}
        ).sort('$natural',-1).limit(1))[0]
        ,
        list(g.db['pub_books'].find(
            {'ex':'QuadrigaCX', 'book':'eth_cad'}
        ).sort('$natural',-1).limit(1))[0]
    ])
