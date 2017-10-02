# app.main.endpoints
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

@main.route('/test/quadcxapi', methods=['GET'])
def _test_quadcx_api():
    """gary_api = g.db['bots'].find_one({'name':'Gary'})['api'][0]
    from app.quadriga import QuadrigaClient
    client = QuadrigaClient(
        api_key=gary_api['key'],
        api_secret=gary_api['secret'],
        client_id=64288,
        default_book='btc_cad'
     )
    #log.debug(client.get_summary())
    #log.debug(client.get_public_orders())
    #log.debug(client.get_trades(limit=5))
    """
    pass
