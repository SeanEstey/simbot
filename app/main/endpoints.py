# app.main.endpoints
from datetime import datetime, timedelta
from dateutil.parser import parse
from bson.json_util import dumps
import logging, pprint
from flask import g, request
log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare
from .simbot import SimBot

@main.route('/indicators/get', methods=['POST'])
def _get_ind():
    get = request.form.get
    series = list(
        g.db['chart_series'].find({
            'ex':get('ex'),
            'pair':(get('asset'), 'cad'),
            'start':{'$gte':datetime.fromtimestamp(int(get('since')))}
        }).sort('start',1)
    )
    return dumps(series)

@main.route('/stats/get', methods=['POST'])
def get_earnings():
    gary = SimBot('Terry')
    return dumps(gary.stats())

@main.route('/holdings/get', methods=['POST'])
def get_holdings():
    bot = SimBot('Terry')
    return dumps(bot.holdings())

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

@main.route('/books/update', methods=['POST'])
def _update_books():
    exchange = request.form.get('exchange')
    if exchange == 'Coinsquare':
        coinsquare.update('CAD', 'BTC')
    return 'OK'
