# app.main.tasks
from time import sleep
from datetime import datetime, timedelta
from dateutil.parser import parse
import json, logging
from pprint import pprint
from app import celery
from flask import g
from app.lib.timer import Timer
from app.main.simulate import SimBot
from app.main import quadcx, coinsquare
from app.main.socketio import smart_emit
from app.quadriga import QuadrigaClient
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def analyze_indicators(self, **rest):
    from app.main.indicators import build_series
    utcnow = datetime.now()+timedelta(hours=6)
    build_series(
        'QuadrigaCX',
        'btc_cad',
        utcnow - timedelta(hours=24),
        utcnow)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_bots(self, **rest):
    gary = SimBot('Terry')
    gary.eval_buy_positions()
    gary.eval_sell_positions()
    gary.eval_arbitrage()

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_exchanges(self, **rest):
    """Get public trades via API, mainly for drawing price charts
    """
    api = g.db['bots'].find_one({'name':'Terry'})['api'][0]
    client = QuadrigaClient(api_key=api['key'], api_secret=api['secret'], client_id=64288)

    for book in ['btc_cad', 'eth_cad']:
        asset = book[0:3]
        n_new = n_total = 0
        for trade in client.get_public_trades(time='hour', book=book):
            r = g.db['pub_trades'].update_one(
                {'tid':trade['tid']},
                {'$set':{
                    'tid':trade['tid'],
                    'exchange':'QuadrigaCX',
                    'currency':asset,
                    'volume':round(float(trade['amount']),5),
                    'price':float(trade['price']),
                    'date':datetime.fromtimestamp(int(trade['date'])+(3600*6)),
                    'side':trade['side']
                }},
                True)
            n_total += 1
            n_new += 1 if r.upserted_id else 0

        if n_new > 0:
            sleep(1)
            orders = client.get_public_orders(book=book)
            for bids in orders['bids']:
                bids[0] = float(bids[0])
                bids[1] = float(bids[1])
            for asks in orders['asks']:
                asks[0] = float(asks[0])
                asks[1] = float(asks[1])
            g.db['pub_books'].insert_one({
                'ex':'QuadrigaCX',
                'book':book,
                'date':datetime.fromtimestamp(int(orders['timestamp'])+(3600*6)),
                'bids':orders['bids'],
                'asks':orders['asks']
            })

            # Update simulation order book.
            quadcx.update('CAD', asset.upper())
            smart_emit('updateTickers',None)
            log.debug('%s/%s new trades, exch=%s, book=%s', n_new, n_total, 'QuadrigaCX', book)
        sleep(5)

















        """v_traded += float(trade['amount'])
        n_sell += 1 if trade['side'] == 'sell' else 0
        n_buy += 1 if trade['side'] == 'buy' else 0
        v_bought += float(trade['amount']) if trade['side'] == 'buy' else 0.0
        v_sold += float(trade['amount']) if trade['side'] == 'sell' else 0.0
        v_ask = v_bid = 0
        ask_delta = [float(orders['asks'][0][0]) * 1.01, None]
        bid_delta = [float(orders['bids'][0][0]) * 0.99, None]
        for b in orders['bids']:
            b[0] = float(b[0])
            b[1] = float(b[1])
            v_bid += b[1]
            if bid_delta[1] is None and b[0] <= bid_delta[0]:
                bid_delta[1] = v_bid
        for a in orders['asks']:
            a[0] = float(a[0])
            a[1] = float(a[1])
            v_ask += a[1]
            if ask_delta[1] is None and a[0] >= ask_delta[0]:
                ask_delta[1] = v_ask
            'analysis': {
                'n_sells':n_sell,
                'n_buys':n_buy,
                'buy_rate':round(n_buy/(n_buy+n_sell),2),
                'v_bought':round(v_bought,5),
                'v_sold':round(v_sold,5),
                'v_traded':round(v_traded,5),
                'v_ask':round(v_ask,5),
                'v_bid':round(v_bid,5),
                'v_ratio': round(v_bid/v_ask,2),
                'ask_inertia':round(ask_delta[1],5),
                'bid_inertia':round(bid_delta[1],5)
            }
        """
