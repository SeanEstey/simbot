# app.main.quadcx
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
    """@base, trade: currency names
    """
    book_name = '%s_%s' %(trade, base)
    update_book(book_name.lower(), base.lower(), trade.lower())
    update_info(book_name.lower(), base.lower(), trade.lower())

#-------------------------------------------------------------------------------
def update_book(book_name, base, trade):
    """Merge order_book data w/ order_book tampered with by simulation.
    """
    conf = exch_conf('QuadrigaCX')
    t1 = Timer()
    try:
        r = requests.get(conf['BOOK_URL'] % book_name)
    except Exception as e:
        log.exception('Failed to get Quadriga orderbook: %s', str(e))
        raise
    else:
        orders = json.loads(r.text)

    bids = [ { 'price':float(x[0]), 'volume':float(x[1]) } for x in orders['bids']]
    asks = [ { 'price':float(x[0]), 'volume':float(x[1]) } for x in orders['asks']]
    spread = round(asks[0]['price'] - bids[0]['price'], 2)


    # Merge bids w/ bid book altered by simulation
    ex = g.db['exchanges'].find_one(
        {'name':'QuadrigaCX', 'book':book_name})

    # Merge order_books. TODO: write this into a separate method.
    n_order_transfers = 0
    old_bids = ex['bids']
    for new_bid in bids:
        b_bid_match = False
        for old_bid in old_bids:
            if old_bid['price'] == new_bid['price'] and old_bid.get('bot_consumed'):
                if new_bid['volume'] > old_bid['volume']:
                    # New order. Old one must have been consumed.
                    continue
                # Assume same order. Update with any volume bot simulation consumed.
                b_bid_match = True
                new_bid['bot_consumed'] = old_bid['bot_consumed']
                new_bid['bot_id'] = old_bid['bot_id']
                new_bid['original'] = old_bid['original']
                n_order_transfers += 1
        if b_bid_match == False:
            new_bid['original'] = new_bid['volume']

    old_asks = ex['asks']
    for new_ask in asks:
        b_ask_match = False
        for old_ask in old_asks:
            if old_ask['price'] == new_ask['price'] and old_ask.get('bot_consumed'):
                if new_ask['volume'] > old_ask['volume']:
                    # New order. Old one must have been consumed.
                    continue
                # Assume same order. Update with any volume bot simulation consumed.
                b_ask_match = True
                new_ask['bot_consumed'] = old_ask['bot_consumed']
                new_ask['bot_id'] = old_ask['bot_id']
                new_ask['original'] = old_ask['original']
                n_order_transfers += 1
        if b_ask_match == False:
            new_ask['original'] = new_ask['volume']

    log.debug('%s tampered orders syncd to new order_books', n_order_transfers)

    r = g.db['exchanges'].update_one(
        {'name':'QuadrigaCX', 'book':book_name},
        {'$set':{
            'name':'QuadrigaCX',
            'base':base,
            'trade':trade,
            'book':book_name,
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
def update_info(book_name, base, trade):
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
        True)
