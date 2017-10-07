# app.main.tasks
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
    gary = SimBot('Gary')
    gary.eval_bids()
    gary.eval_asks()
    gary.eval_arbitrage()
    #smart_emit('updateBot',None)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_exchanges(self, **rest):
    """Get public trades via API, mainly for drawing price charts
    """
    from app.quadriga import QuadrigaClient
    gary_api = g.db['bots'].find_one({'name':'Gary'})['api'][0]

    client = QuadrigaClient(
        api_key=gary_api['key'], api_secret=gary_api['secret'], client_id=64288,
        default_book='btc_cad')

    for book in ['btc_cad', 'eth_cad']:
        asset = book[0:3]
        n_new_trades = 0
        n=0
        for trade in client.get_public_trades(time='hour', book=book):
            r = g.db['trades'].update_one(
                {'tid':trade['tid']},
                {'$set':{
                    'tid':trade['tid'],
                    'exchange':'QuadrigaCX',
                    'currency':asset,
                    'volume':round(float(trade['amount']),5),
                    'price':float(trade['price']),
                    'date':datetime.fromtimestamp(int(trade['date'])),
                    'side':trade['side']
                }},
                True)
            n_new_trades += 1 if r.upserted_id else 0
            n+=1

        if n_new_trades > 0:
            # Update order book and ticker
            quadcx.update('CAD', asset.upper())
            smart_emit('updateTickers',None)

            log.debug('%s/%s new trades, exch=%s, book=%s',
                n_new_trades, n, 'QuadrigaCX', book)
