# pub_data.py
import logging
from time import sleep
from datetime import datetime
from app import celery
from flask import g
from app.main import quadcx
from app.main.socketio import smart_emit
from app.quadriga import QuadrigaClient
log = logging.getLogger(__name__)

API_BOT_NAME = 'Terry'
BOOKS = ['btc_cad', 'eth_cad']
EX = ['QuadrigaCX']
CLIENT_ID=64288

#---------------------------------------------------------------
def save_trades():
    for ex in EX:
        api = g.db['sim_bots'].find_one({'name':API_BOT_NAME})['api'][0]
        client = QuadrigaClient(api_key=api['key'], api_secret=api['secret'], client_id=CLIENT_ID)

        for book in BOOKS:
            n_new = n_total = 0
            for trade in client.get_public_trades(time='minute', book=book):
                r = g.db['pub_trades'].update_one(
                    {'tid':trade['tid']},
                    {'$set':{
                        'tid':trade['tid'],
                        'ex':'QuadrigaCX',
                        'book':book,
                        'volume':round(float(trade['amount']),5),
                        'price':float(trade['price']),
                        'date':datetime.fromtimestamp(int(trade['date'])+(3600*6)),
                        'side':trade['side']
                    }},
                    True)
                n_total += 1
                n_new += 1 if r.upserted_id else 0

            if n_new > 0:
                # Update simulation order book.
                #asset = book[0:3]
                #quadcx.update('CAD', asset.upper())
                #smart_emit('updateTickers',None)
                #log.debug('%s/%s new trades, exch=%s, book=%s', n_new, n_total, 'QuadrigaCX', book)
                pass

#---------------------------------------------------------------
def save_orderbook():
    for ex in EX:
        api = g.db['sim_bots'].find_one({'name':API_BOT_NAME})['api'][0]
        client = QuadrigaClient(api_key=api['key'], api_secret=api['secret'], client_id=CLIENT_ID)

        for book in BOOKS:
            orders = client.get_public_orders(book=book)

            for bids in orders['bids']:
                bids[0] = float(bids[0])
                bids[1] = float(bids[1])
            for asks in orders['asks']:
                asks[0] = float(asks[0])
                asks[1] = float(asks[1])

            g.db['pub_books'].insert_one({
                'ex':ex,
                'book':book,
                'date':datetime.fromtimestamp(int(orders['timestamp'])+(3600*6)),
                'bids':orders['bids'],
                'asks':orders['asks']
            })
