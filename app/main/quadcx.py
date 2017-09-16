# app.main.cbix
import json
import requests
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def ticker():
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """

    from config import QUADCX
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
def order_books():
    """Save recent orderbook to DB
    """

    from config import QUADCX
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
                'bids': [ [ float(x[0]), float(x[1]) ] for x in orders['bids']],
                'asks': [ [ float(x[0]), float(x[1]) ] for x in orders['asks']]
            }},
            True)

        log.info('quadcx.%s book, bids=%s, asks=%s [%sms]',
            book['name'], len(orders['bids']), len(orders['asks']), t1.clock(t='ms'))
        t1.restart()
