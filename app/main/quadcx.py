# app.main.quadcx
import json
import requests
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
from app.main import exch_conf
from . import books
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update(base, trade):
    """Update order books and ticker.
    :base, trade: currency names
    """
    book_name = '%s_%s' %(trade, base)
    update_order_book(book_name.lower(), base.lower(), trade.lower())
    update_ticker(book_name.lower(), base.lower(), trade.lower())

#-------------------------------------------------------------------------------
def update_order_book(book_name, base, trade):
    conf = exch_conf('QuadrigaCX')
    t1 = Timer()

    try:
        r = requests.get(conf['BOOK_URL'] % book_name)
    except Exception as e:
        log.exception('Failed to get Quadriga orderbook: %s', str(e))
        raise
    else:
        data = json.loads(r.text)

    orders = {
        'bids': [
            { 'price':float(x[0]), 'volume':float(x[1]) } for x in data['bids']
        ],
        'asks': [
            { 'price':float(x[0]), 'volume':float(x[1]) } for x in data['asks']
        ]
    }

    # TODO: Move to update_ticker()
    spread = round(orders['asks'][0]['price'] - orders['bids'][0]['price'], 2)
    books.merge(orders, 'QuadrigaCX', book_name, base, trade, spread)
    #pprint('QuadrigaCX bid=%s, ask=%s, spread=%s [%sms]' %(
    #    orders['bids'][0]['price'], orders['asks'][0]['price'], spread, t1.clock(t='ms')))

#-------------------------------------------------------------------------------
def update_ticker(book_name, base, trade):
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """
    conf = exch_conf('QuadrigaCX')
    t1 = Timer()
    try:
        r = requests.get(conf['TICKER_URL'] % book_name)
    except Exception as e:
        log.exception('Failed to get Quadriga ticker book: %s', str(e))
        raise
    else:
        data = json.loads(r.text)

    for k in data:
        data[k] = float(data[k])

    data.update({'name':'QuadrigaCX'})

    #spread = round(orders['asks'][0]['price'] - orders['bids'][0]['price'], 2)

    res = g.db['trades'].find(
        {'exchange':'QuadrigaCX', 'currency':trade}
    ).sort('$natural',-1).limit(1)
    if res.count() > 0:
        last = res[0]['price']
    else:
        last = False

    r = g.db['exchanges'].update_one(
        {'name':'QuadrigaCX', 'book':book_name},
        {'$set':{
            'base':base,
            'trade':trade,
            'volume':float(data['volume']),
            'high':float(data['high']),
            'low':float(data['low']),
            'last':last
        }},
        True
    )
