# app.main.endpoints
from datetime import datetime, timedelta
from dateutil.parser import parse
from bson.json_util import dumps
import logging, pprint
from flask import g, request
log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare
from .simulate import SimBot

@main.route('/ind/test', methods=['GET'])
def _test_ind():
    from app.main.indicators import build_series
    utcnow = datetime.now()+timedelta(hours=6)
    build_series(
        'QuadrigaCX',
        'btc_cad',
        utcnow - timedelta(hours=24),
        utcnow)
    return 'ok'

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

@main.route('/books/update', methods=['POST'])
def _update_books():
    exchange = request.form.get('exchange')
    if exchange == 'Coinsquare':
        coinsquare.update('CAD', 'BTC')
    return 'OK'
