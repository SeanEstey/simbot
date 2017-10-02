# app.main.coinsqare
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
    conf = exch_conf('Coinsquare')
    t1 = Timer()
    try:
        data = requests.get(conf['BOOK_URL'] % (base.upper(),trade.upper()))
    except Exception as e:
        log.exception('Coinsquare orderbook request failed: %s', str(e))
        return False
    else:
        pprint(data)
        _book = json.loads(data.text)['book']
        asks = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 'b']
        del asks[-1]
        bids = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 's']
        del bids[-1]

    book = {'name':'Coinsquare', 'bids':[], 'asks':[]}

    for ask in asks:
        dollars = float(ask['amt'])/100
        volume = float(ask['base'])/100000000
        price = round(dollars/volume,2)
        book['asks'].append({'price':price, 'volume':round(volume,5)})

    for bid in bids:
        dollars = float(bid['amt'])/100
        volume = float(bid['base'])/100000000
        price = round(dollars/volume,2)
        book['bids'].append({'price':price, 'volume':round(volume,5)})

    spread = round(book['asks'][0]['price'] - book['bids'][0]['price'], 2)

    books.merge(book, 'Coinsquare', book_name, base, trade, spread)

    pprint('Coinsquare bid=%s, ask=%s, spread=%s [%sms]' %(
        book['bids'][0]['price'], book['asks'][0]['price'], spread, t1.clock(t='ms')))

#-------------------------------------------------------------------------------
def update_ticker(book_name, base, trade):
    """
    res = g.db['trades'].find(
        {'exchange':'Coinsquare', 'currency':trade}
    ).sort('$natural',-1).limit(1)
    if res.count() >0:
        last = res[0]['price']
    else:
        last = False
    """
    pass
