# app.main.tasks
import json, logging
from pprint import pprint
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)
from app.main.simulate import SimBot
from app.main import quadcx, coinsquare

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update(self, **rest):
    # Update market data
    quadcx.update('CAD','BTC')
    quadcx.update('CAD','ETH')
    coinsquare.update('CAD','BTC')

    # Go Garybot!
    gary = SimBot('Gary')
    gary.eval_bids()
    gary.eval_asks()
    gary.eval_arbitrage()

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def api_update(self, **rest):
    from app.quadriga import QuadrigaClient
    from datetime import datetime

    book='eth_cad'
    asset='eth'

    gary_api = g.db['bots'].find_one({'name':'Gary'})['api'][0]
    client = QuadrigaClient(
        api_key=gary_api['key'],
        api_secret=gary_api['secret'],
        client_id=64288,
        default_book=book
    )
    trades = client.get_public_trades(time='hour')
    for trade in trades:
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
            True
        )
        if r.modified_count and r.modified_count > 0:
            log.info('QuadrigaCX eth_cad, p=%s, v=%s', trade['price'], trade['volume'])

    log.debug('pulled %s eth_cad trades', len(trades))
