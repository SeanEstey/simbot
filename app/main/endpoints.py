# app.main.endpoints
from bson.json_util import dumps
import logging, pprint
from flask import g, request
log = logging.getLogger(__name__)
from . import main
from . import simbot

@main.route('/tickers', methods=['POST'])
def get_tickers():
    tickers = list(g.db['tickers'].find())
    return dumps(tickers)

@main.route('/orders', methods=['POST'])
def get_orders():
    orders = list(g.db['orders'].find()).limit(100).sort('date',-1)
    return dumps(orders)

@main.route('/trades', methods=['POST'])
def get_trades():
    trades = list(g.db['trades'].find()).limit(100).sort('date',-1)
    return dumps(trades)

@main.route('/trade/process', methods=['POST'])
def _process_trade():
    simbot.process_trade(request.form.get('trade_id'))
    return 'OK'
