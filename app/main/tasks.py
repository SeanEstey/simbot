# app.main.tasks
from time import sleep
from datetime import datetime
import json, logging
from pprint import pprint
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)
from app.main.simulate import SimBot
from app.main import quadcx, coinsquare
from app.main.socketio import smart_emit

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
    from app.quadriga import QuadrigaClient
    gary_api = g.db['bots'].find_one({'name':'Terry'})['api'][0]

    client = QuadrigaClient(
        api_key=gary_api['key'], api_secret=gary_api['secret'], client_id=64288,
        default_book='btc_cad')

    for book in ['btc_cad', 'eth_cad']:
        asset = book[0:3]
        n = n_buy = n_sell = n_new_trades = v_traded = v_bought = v_sold = 0
        trades = client.get_public_trades(time='hour',book=book)
        for trade in trades:
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
            v_traded += float(trade['amount'])
            n_sell += 1 if trade['side'] == 'sell' else 0
            n_buy += 1 if trade['side'] == 'buy' else 0
            v_bought += float(trade['amount']) if trade['side'] == 'buy' else 0.0
            v_sold += float(trade['amount']) if trade['side'] == 'sell' else 0.0
            n_new_trades += 1 if r.upserted_id else 0
            n+=1

        if n_new_trades > 0:
            sleep(1)
            summary = client.get_summary(book=book)
            sleep(1)
            orders = client.get_public_orders(book=book)

            # Total order book volumes
            # Volume required to shift price by >= 1%
            v_ask = v_bid = 0
            ask_delta = [float(orders['asks'][0][0]) * 1.01, None]
            bid_delta = [float(orders['bids'][0][0]) * 0.99, None]

            for b in orders['bids']:
                v_bid += float(b[1])
                if bid_delta[1] is None and float(b[0]) <= bid_delta[0]:
                    bid_delta[1] = v_bid

            for a in orders['asks']:
                v_ask += float(a[1])
                if ask_delta[1] is None and float(a[0]) >= ask_delta[0]:
                    ask_delta[1] = v_ask

            g.db['pub_books'].insert_one({
                'ex':'QuadrigaCX',
                'book':book,
                'date':datetime.fromtimestamp(int(orders['timestamp'])+(3600*6)),
                'summary':summary,
                'bids':orders['bids'],
                'asks':orders['asks'],
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
            })

            # Update simulation order book.
            quadcx.update('CAD', asset.upper())
            smart_emit('updateTickers',None)

            log.debug('%s/%s new trades, exch=%s, book=%s',
                n_new_trades, n, 'QuadrigaCX', book)

        sleep(5)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def analyze_recent_trades(self, **rest):
    """Run every 10 min?


    'n_sell_mkt_orders':n_sell,
    'n_buy_mkt_orders':n_buy,
    'buy_ratio': round(n_buy/(n_buy+n_sell),2)
    'v_traded':94994,
    'ra_bid_ask_v': # average
    """

    pass
