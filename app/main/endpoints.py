# app.main.endpoints
from datetime import datetime, timedelta
from bson.json_util import dumps
import logging, pprint
from flask import g, request
log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare
from .simulate import SimBot

@main.route('/stats/get', methods=['POST'])
def get_earnings():
    gary = SimBot('Gary')
    return dumps(gary.stats())

@main.route('/holdings/get', methods=['POST'])
def get_holdings():
    gary = SimBot('Gary')
    holdings = gary.holdings()
    return dumps(holdings)

@main.route('/tickers/get', methods=['POST'])
def get_tickers():
    tickers = list(g.db['exchanges'].find())
    return dumps(tickers)

@main.route('/orders/get', methods=['POST'])
def get_orders():
    orders = list(g.db['orders'].find()).limit(100).sort('date',-1)
    return dumps(orders)

@main.route('/trades/get', methods=['POST'])
def get_trades():
    exchange = request.form.get('exchange')
    asset = request.form.get('asset')
    start = datetime.fromtimestamp(int(request.form.get('since')))
    trades = list(
        g.db['trades'].find({
            'exchange':exchange,
            'currency':asset,
            'date':{'$gte':start}
        }).sort('date',1)
    )
    return dumps(trades)

@main.route('/books/update', methods=['POST'])
def _update_books():
    exchange = request.form.get('exchange')
    if exchange == 'Coinsquare':
        coinsquare.update('CAD', 'BTC')
    return 'OK'
