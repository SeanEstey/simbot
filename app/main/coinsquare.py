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
        asks = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 'b']
        del asks[-1]
        bids = [_book[i] for i in range(len(_book)) if _book[i]['t'] == 's']
        del bids[-1]

    book = {'name':'Coinsquare', 'bids':[], 'asks':[]}

    for ask in asks:
        dollars = float(ask['amt'])/100
        volume = round(float(ask['base'])/100000000, 5)
        price = round(dollars/volume,2)
        book['asks'].append({'price':price, 'volume':volume})

    for bid in bids:
        dollars = float(bid['amt'])/100
        volume = round(float(bid['base'])/100000000, 5)
        price = round(dollars/volume,2)
        book['bids'].append({'price':price, 'volume':volume})

    spread = round(book['asks'][0]['price'] - book['bids'][0]['price'], 2)



    # Merge order_books. TODO: write this into a separate method.
    ex = g.db['exchanges'].find_one(
        {'name':'Coinsquare', 'book':book_name})
    n_order_transfers = 0
    old_bids = ex['bids']
    for new_bid in book['bids']:
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
    for new_ask in book['asks']:
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
