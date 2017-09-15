# quadrigacx.py

import json
import logging
import requests
from pprint import pprint
from flask import g
import numpy as np
from app.lib.timer import Timer
log = logging.getLogger(__name__)

from config import CBIX, QUADCX

#-------------------------------------------------------------------------------
def cbix():

        try:
            r = requests.get(CBIX['url'])
        except Exception as e:
            log.exception('Failed to get Quadriga ticker book: %s', str(e))
            raise
        else:
            data = json.loads(r.text)

        low = high = data['exchanges'][0]

        for i in range(len(data['exchanges'])):
            exch = data['exchanges'][i]
            exch.update({
                'ask':float(exch['ask']),
                'bid':float(exch['bid']),
                'last':float(exch['last'])
            })
            if exch['last'] > high['last']:
                high = exch
            elif exch['last'] < low['last']:
                low = exch

        data['spread'] = {
            'high':high['last'],
            'low':low['last'],
            'diff': high['last']-low['last']
        }

        r = g.db['ticker'].update_one(
            {'source':data['source']},
            {'$set':data},
            True
        )

        log.info('%s tickers updated, spread=%s',
            len(data['exchanges']), data['spread']['diff'])


#-------------------------------------------------------------------------------
def quadcx_ticker():
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """

    t1 = Timer()
    books = QUADCX['books']
    for i in range(len(books)):
        data = {}
        book = books[i]

        try:
            r = requests.get('%s?book=%s' % (QUADCX['ticker_url'], book['name']))
        except Exception as e:
            log.exception('Failed to get Quadriga ticker book: %s', str(e))
            raise
        else:
            data = json.loads(r.text)

        for k in data:
            data[k] = float(data[k])
        data.update({
            'exchange': QUADCX['name'],
            'book':book
        })

        r = g.db['ticker'].update_one(
            {'exchange':QUADCX['name'], 'book':book},
            {'$set':data},
            True
        )

        log.info('quadcx.%s ticker last=%s, bid=%s, ask=%s [%sms]',
            book['name'], data['last'], data['bid'], data['ask'], t1.clock(t='ms'))
        t1.restart()

#-------------------------------------------------------------------------------
def quadcx_books():
    """Save recent orderbook to DB
    """

    t1 = Timer()
    books = QUADCX['books']

    for i in range(len(books)):
        book = books[i]

        try:
            r = requests.get('%s?book=%s' % (QUADCX['books_url'], book['name']))
        except Exception as e:
            log.exception('Failed to get Quadriga orderbook: %s', str(e))
            raise
        else:
            orders = json.loads(r.text)

        # Update/upsert orders
        r = g.db['order_books'].update_one(
            {'exchange':QUADCX['name'], 'book':book},
            {'$set':{
                'exchange': QUADCX['name'],
                'book': book,
                'timestamp': int(orders['timestamp']),
                'bids': np.array(orders['bids']).tolist(),
                'asks': np.array(orders['asks']).tolist()
            }},
            True)

        log.info('quadcx.%s book, bids=%s, asks=%s [%sms]',
            book['name'], len(orders['bids']), len(orders['asks']), t1.clock(t='ms'))
        t1.restart()
