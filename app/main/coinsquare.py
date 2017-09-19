# app.main.coinsqare
import json
import requests
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update_books():

    t1 = Timer()

    try:
        data = requests.get('https://coinsquare.io/api/v1/data/bookandsales/CAD/BTC/16?')
    except Exception as e:
        log.exception('Coinsquare orderbook request failed: %s', str(e))
        return False
    else:
        _book = json.loads(data.text)['book']
        _asks = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 'b']
        del _asks[-1]
        _bids = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 's']
        del _bids[-1]

    book = {
        'exchange': 'Coinsquare',
        'bids': [],
        'asks': [],
    }

    for ask in _asks:
        dollars = float(ask['amt'])/100
        volume = round(float(ask['base'])/100000000, 5)
        price = round(dollars/volume,2)
        book['asks'].append({'price':price, 'volume':volume})

    for bid in _bids:
        dollars = float(bid['amt'])/100
        volume = round(float(bid['base'])/100000000, 5)
        price = round(dollars/volume,2)
        book['bids'].append({'price':price, 'volume':volume})

    spread = round(book['asks'][0]['price'] - book['bids'][0]['price'], 2)

    g.db['exchanges'].update_one(
        {'name':'Coinsquare'},
        {'$set':{
            'name':'Coinsquare',
            'bids':book['bids'],
            'asks':book['asks'],
            'bid':book['bids'][0]['price'],
            'ask':book['asks'][0]['price'],
            'spread':spread
        }},
        True
    )

    pprint('Coinsquare bid=%s, ask=%s, spread=%s [%sms]' %(
        book['bids'][0]['price'], book['asks'][0]['price'], spread, t1.clock(t='ms')))
