# pub_data.py
import logging
from time import sleep
from datetime import datetime
from app import celery
from flask import g
from bson.json_util import dumps
from app.main import ex_confs
from app.main import quadcx
from app.main.socketio import smart_emit
from app.quadriga import QuadrigaClient
from config import ACTIVE_SIM_BOT
log = logging.getLogger(__name__)

#---------------------------------------------------------------
def save_tickers():
    quadcx.update_ticker(('btc','cad'))
    quadcx.update_ticker(('eth','cad'))

#---------------------------------------------------------------
def save_trades():
    for conf in ex_confs():
        api = g.db['sim_bots'].find_one({'name':ACTIVE_SIM_BOT})['api'][0]
        client = QuadrigaClient(
            api_key=api['key'],
            api_secret=api['secret'],
            client_id=conf['CLIENT_ID'])

        for pair in conf['PAIRS']:
            n_new = n_total = 0
            book = conf['PAIRS'][pair]['book']

            for trade in client.get_public_trades(time='minute', book=book):
                r = g.db['pub_trades'].update_one(
                    {'tid':trade['tid']},
                    {'$set':{
                        'tid':trade['tid'],
                        'ex':conf['NAME'],
                        'pair':pair,
                        'volume':round(float(trade['amount']),5),
                        'price':float(trade['price']),
                        'date':datetime.fromtimestamp(int(trade['date'])+(3600*6)),
                        'side':trade['side']
                    }},
                    True)
                n_total += 1
                if r.upserted_id:
                    trade['ex'] = conf['NAME']
                    trade['pair'] = pair
                    smart_emit('updateGraphStream', dumps({'type':'trade', 'data':trade}))
                    n_new+=1
                #log.debug('%s/%s new trades, exch=%s, book=%s', n_new, n_total, 'QuadrigaCX', book)

#---------------------------------------------------------------
def save_orderbook():
    for conf in ex_confs():
        api = g.db['sim_bots'].find_one({'name':ACTIVE_SIM_BOT})['api'][0]
        client = QuadrigaClient(
            api_key=api['key'],
            api_secret=api['secret'],
            client_id=conf['CLIENT_ID'])

        for pair in conf['PAIRS']:
            orders = client.get_public_orders(book=conf['PAIRS'][pair]['book'])

            for bids in orders['bids']:
                bids[0] = float(bids[0])
                bids[1] = float(bids[1])
            for asks in orders['asks']:
                asks[0] = float(asks[0])
                asks[1] = float(asks[1])

            document = {
                'ex':conf['NAME'],
                'pair':pair,
                'date':datetime.fromtimestamp(int(orders['timestamp'])+(3600*6)),
                'bids':orders['bids'],
                'asks':orders['asks']
            }

            g.db['pub_books'].insert_one(document)
            smart_emit('updateGraphStream', dumps({'type':'orderbook', 'data':document}))
