# app.main.cbix
import json
import requests
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update_books():
    """Save recent orderbook to DB
    """

    t1 = Timer()
    book_name = 'btc_cad'

    try:
        r = requests.get('https://api.quadrigacx.com/v2/order_book?book='+book_name)
    except Exception as e:
        log.exception('Failed to get Quadriga orderbook: %s', str(e))
        raise
    else:
        orders = json.loads(r.text)

    bids = [ { 'price':float(x[0]), 'volume':float(x[1]) } for x in orders['bids']]
    asks = [ { 'price':float(x[0]), 'volume':float(x[1]) } for x in orders['asks']]
    spread = round(asks[0]['price'] - bids[0]['price'], 2)

    r = g.db['exchanges'].update_one(
        {'name':'QuadrigaCX'},
        {'$set':{
            'name': 'QuadrigaCX',
            'book': book_name,
            'timestamp': int(orders['timestamp']),
            'bids':bids,
            'asks':asks,
            'bid': bids[0]['price'],
            'ask': asks[0]['price'],
            'spread':spread
        }},
        True)

    pprint('QuadrigaCX bid=%s, ask=%s, spread=%s [%sms]' %(
        bids[0]['price'], asks[0]['price'], spread, t1.clock(t='ms')))

#-------------------------------------------------------------------------------
def ticker():
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """

    url = 'https://api.quadrigacx.com/v2/ticker', # ?book=bname
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
