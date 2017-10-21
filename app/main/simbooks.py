# simbooks.py
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

EX = ['QuadrigaCX']
BOOKS = ['btc_cad', 'eth_cad']

#-------------------------------------------------------------------------------
def merge_all():
    for ex in EX:
        for book in BOOKS:
            docs = g.db['pub_books'].find({'ex':ex, 'book':book}).sort('date',-1).limit(1)
            doc = list(docs)[0]
            orders = {'bids':doc['bids'], 'asks':doc['asks']}
            merge(orders, ex, book, book[4:7], book[0:3], 0)

#-------------------------------------------------------------------------------
def get_bid(exch, pair):
    """Find the highest bid price/volume not consumed by simulation.
    """
    bids = g.db['sim_books'].find_one({'name':exch, 'book':pair})['bids']
    idx=0
    while idx<len(bids):
        bid = bids[idx]
        vol_remain = bid['original'] - bid.get('bot_consumed',0)
        if vol_remain > 0:
            return {'price':bid['price'], 'volume':vol_remain}
        idx+=1
    return None

def fill_limit_order(ex, pair):
    pass


#-------------------------------------------------------------------------------
def get_ask(exch, pair):
    """Find the lowest ask price/vol not consumed by simulation.
    """
    asks = g.db['sim_books'].find_one({'name':exch, 'book':pair})['asks']
    idx=0
    while idx<len(asks):
        ask = asks[idx]
        vol_remain = ask['original'] - ask.get('bot_consumed',0)
        if vol_remain > 0:
            return {'price':ask['price'], 'volume':vol_remain}
        idx+=1
    return None

#-------------------------------------------------------------------------------
def update(ex_name, pair, section, bot_id, vol_consumed):
    """Update order book w/ simulated order.
    TODO: add support for consuming multiple orders.

    :pair: currency pair (str)
        'btc_cad', 'eth_cad', etc
    :section: book section (str)
        'bids' or 'asks'
    """
    ex = g.db['sim_books'].find_one({'name':ex_name, 'book':pair})
    order = ex[section][0]

    if order.get('bot_consumed'):
        order['bot_consumed'] += vol_consumed
    else:
        order['bot_consumed'] = vol_consumed

    order['bot_id'] = bot_id
    ex[section][0] = order

    g.db['sim_books'].update_one(
        {'_id':ex['_id']},
        {'$set':{
            section: ex[section]
        }}
    )

#-------------------------------------------------------------------------------
def merge(orders, ex_name, book_name, base, trade, spread):
    """Merge real order books w/ simulated books.

    :orders: sorted order book (dict).
        {'bids':[], 'asks':[]}
    """
    n_matches = 0
    ex = g.db['sim_books'].find_one({'name':ex_name, 'book':book_name})
    new_orders = {'asks':[], 'bids':[]}

    for section in ['bids', 'asks']:
        for order in orders[section]:
            b_match = False
            for db_order in ex[section]:
                if db_order['price'] == order[0] and db_order.get('bot_consumed'):
                    # Assume order is new if volume increase at matching order price.
                    if order[1] > db_order['volume']:
                        continue
                    # Merge updated order volume w/ volume consumed by simulation.

                    new_orders[section].append({
                        'price':db_order['price'],
                        'bot_consumed':db_order['bot_consumed'],
                        'bot_id':db_order['bot_id'],
                        'original':db_order['original'],
                        'volume':db_order['original']
                    })
                    b_match = True
                    n_matches += 1
            if b_match == False:
                new_orders[section].append({
                    'price': order[0],
                    'volume': order[1],
                    'original': order[1]
                })
    #log.debug('books.merge: %s modified orders syncd to new order_books', n_matches)
    #log.debug(new_orders)

    r = g.db['sim_books'].update_one(
        {'name':ex_name, 'book':book_name},
        {'$set':{
            'name':ex_name,
            'base':base,
            'trade':trade,
            'book':book_name,
            'bids':new_orders['bids'],
            'asks':new_orders['asks'],
            'bid': new_orders['bids'][0]['price'],
            'ask': new_orders['asks'][0]['price'],
            'spread':spread
        }},
        True
    )
