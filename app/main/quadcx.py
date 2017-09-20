# app.main.cbix
import json
import requests
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update_books(book_name):
    """Save recent orderbook to DB
    """
    t1 = Timer()

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
def update_info(book_name):
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """
    t1 = Timer()

    try:
        r = requests.get('https://api.quadrigacx.com/v2/ticker?book=%s' % book_name)
    except Exception as e:
        log.exception('Failed to get Quadriga ticker book: %s', str(e))
        raise
    else:
        data = json.loads(r.text)

    for k in data:
        data[k] = float(data[k])

    data.update({
        'name': 'QuadrigaCX',
    })

    last = g.db['trades'].find({'exchange':'QuadrigaCX'}).sort('$natural',-1).limit(1)[0]['price']

    r = g.db['exchanges'].update_one(
        {'name':'QuadrigaCX'},
        {'$set':{
            'volume':float(data['volume']),
            'high':float(data['high']),
            'low':float(data['low']),
            'last':last
        }},
        True
    )

    log.info('quadcx last=$%s, bid=$%s, ask=$%s [%sms]',
        data['last'], data['bid'], data['ask'], t1.clock(t='ms'))
