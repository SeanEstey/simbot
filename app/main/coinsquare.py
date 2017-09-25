# app.main.coinsqare
import json
import requests
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
from app.main import exch_conf
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update(base, trade):
    book_name = '%s_%s' %(trade, base)
    update_book(book_name.lower(), base, trade)

#-------------------------------------------------------------------------------
def update_book(book_name, base, trade):
    conf = exch_conf('Coinsquare')
    t1 = Timer()
    try:
        data = requests.get(conf['BOOK_URL'] % (base,trade))
    except Exception as e:
        log.exception('Coinsquare orderbook request failed: %s', str(e))
        return False
    else:
        pprint(data)
        _book = json.loads(data.text)['book']
        _asks = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 'b']
        del _asks[-1]
        _bids = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 's']
        del _bids[-1]

    book = {'name':'Coinsquare', 'bids':[], 'asks':[]}

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

    res = g.db['trades'].find(
        {'exchange':'Coinsquare', 'currency':trade}
    ).sort('$natural',-1).limit(1)
    if res.count() >0:
        last = res[0]['price']
    else:
        last = False

    # TODO: find 'high', 'low', 'volume', etc values somwhere
    g.db['exchanges'].update_one(
        {'name':'Coinsquare', 'book':book_name},
        {'$set':{
            'name':'Coinsquare',
            'base':base.lower(),
            'trade':trade.lower(),
            'book':book_name,
            'bid':book['bids'][0]['price'],
            'last':last,
            'ask':book['asks'][0]['price'],
            'spread':spread,
            'bids':book['bids'],
            'asks':book['asks']
        }},
        True)
    pprint('Coinsquare bid=%s, ask=%s, spread=%s [%sms]' %(
        book['bids'][0]['price'], book['asks'][0]['price'], spread, t1.clock(t='ms')))
