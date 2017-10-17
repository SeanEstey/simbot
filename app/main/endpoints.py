# app.main.endpoints
from datetime import datetime, timedelta
from bson.json_util import dumps
import logging, pprint
from flask import g, request

log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare
from .simulate import SimBot
from .indicators import get_book_metrics, get_trade_metrics

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


@main.route('/indicators/book', methods=['POST'])
def _get_book_ind():
    get = request.form.get
    return get_book_metrics(
        get('ex'),
        '%s_cad' % get('asset'),
        get('ykey'),
        datetime.fromtimestamp(int(get('since'))),
        datetime.fromtimestamp(int(get('until')))
    )

@main.route('/indicators/trade', methods=['POST'])
def _get_ind():
    get = request.form.get
    return get_trade_metrics(
        get('ex'),
        '%s_cad' % get('asset'),
        get('ykey'),
        datetime.fromtimestamp(int(get('since'))),
        datetime.fromtimestamp(int(get('until')))
    )
