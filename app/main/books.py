# books.py
from logging import getLogger
from flask import g
from app.lib.timer import Timer

log = getLogger(__name__)

#-------------------------------------------------------------------------------
def order_vol(ex_name, pair, section, price=None):
    """Volume remaining for highest bid/lowest ask adjusted for simulation
    consumption.
    """
    if price:
        k = section[0:-1]
        ex_doc = g.db['exchanges'].find_one({'name':ex_name, 'book':pair, k:price})
    else:
        ex_doc = g.db['exchanges'].find_one({'name':ex_name, 'book':pair})
    top_order = ex_doc[section][0]
    vol_left = top_order['original'] - top_order.get('bot_consumed',0)
    log.debug('%s %s vol_left=%s/%s',
        ex_name, section[0:-1], round(vol_left,2), round(top_order['original'],2))
    return vol_left

#-------------------------------------------------------------------------------
def update(ex_name, pair, section, bot_id, vol_consumed):
    """Update order book w/ simulated order.
    TODO: add support for consuming multiple orders.

    :pair: currency pair (str)
        'btc_cad', 'eth_cad', etc
    :section: book section (str)
        'bids' or 'asks'
    """
    ex = g.db['exchanges'].find_one({'name':ex_name, 'book':pair})
    order = ex[section][0]

    if order.get('bot_consumed'):
        order['bot_consumed'] += vol_consumed
    else:
        order['bot_consumed'] = vol_consumed

    order['bot_id'] = bot_id
    ex[section][0] = order

    g.db['exchanges'].update_one(
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
    ex = g.db['exchanges'].find_one({'name':ex_name, 'book':book_name})

    for section in ['bids', 'asks']:
        for order in orders[section]:
            b_match = False
            for db_order in ex[section]:
                if db_order['price'] == order['price'] and db_order.get('bot_consumed'):
                    # Assume order is new if volume increase at matching order price.
                    if order['volume'] > db_order['volume']:
                        continue
                    # Merge updated order volume w/ volume consumed by simulation.
                    order.update({
                        'bot_consumed':db_order['bot_consumed'],
                        'bot_id':db_order['bot_id'],
                        'original':db_order['original']
                    })
                    b_match = True
                    n_matches += 1
            if b_match == False:
                order['original'] = order['volume']

    #log.debug('books.merge: %s modified orders syncd to new order_books', n_matches)

    r = g.db['exchanges'].update_one(
        {'name':ex_name, 'book':book_name},
        {'$set':{
            'name':ex_name,
            'base':base,
            'trade':trade,
            'book':book_name,
            'bids':orders['bids'],
            'asks':orders['asks'],
            'bid': orders['bids'][0]['price'],
            'ask': orders['asks'][0]['price'],
            'spread':spread
        }},
        True
    )
