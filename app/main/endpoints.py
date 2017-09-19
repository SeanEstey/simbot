# app.main.endpoints
from bson.json_util import dumps
import logging, pprint
from flask import g, request
log = logging.getLogger(__name__)
from . import main
from . import quadcx, coinsquare, simbot

@main.route('/tickers/get', methods=['POST'])
def get_tickers():
    tickers = list(g.db['tickers'].find())
    return dumps(tickers)

@main.route('/orders/get', methods=['POST'])
def get_orders():
    orders = list(g.db['orders'].find()).limit(100).sort('date',-1)
    return dumps(orders)

@main.route('/trades/get', methods=['POST'])
def get_trades():
    trades = list(g.db['trades'].find()).limit(100).sort('date',-1)
    return dumps(trades)

@main.route('/books/update', methods=['POST'])
def _update_books():
    exchange = request.form.get('exchange')

    if exchange == 'Coinsquare':
        coinsquare.update_books()
    elif exchange == 'QuadrigaCX':
        quadcx.update_books()

    return 'OK'
