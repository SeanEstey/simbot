# simbooks.py
from logging import getLogger
from flask import g
from app.lib.timer import Timer
from app.main import ex_confs
log = getLogger(__name__)

EX = ['QuadrigaCX']
BOOKS = ['btc_cad', 'eth_cad']

#-------------------------------------------------------------------------------
def merge_all():
    """Merge updated public order book data with simulation order books.
    """
    for conf in ex_confs():
        for pair in conf['PAIRS']:
            pub_book = list(
                g.db['pub_books'].find({'ex':conf['NAME'], 'pair':pair}).sort('date',-1).limit(1)
            )[0]

            merge(conf['NAME'], pair, pub_book['bids'], pub_book['asks'])

#-------------------------------------------------------------------------------
def get_bid(ex, pair):
    """Find the highest bid price/volume not consumed by simulation.
    :pair: ('btc','cad') tuple
    """
    bids = g.db['sim_books'].find_one({'ex':ex, 'pair':pair})['bids']
    idx=0
    while idx<len(bids):
        if bids[idx][1] > 0:
            return bids[idx]
        idx+=1
    return None

#-------------------------------------------------------------------------------
def get_ask(ex, pair):
    """Find the lowest ask price/vol not consumed by simulation.
    """
    asks = g.db['sim_books'].find_one({'ex':ex, 'pair':pair})['asks']
    idx=0
    while idx<len(asks):
        if asks[idx][1] > 0:
            return asks[idx]
        idx+=1
    return None

#-------------------------------------------------------------------------------
def update(ex, pair, section, bot_id, vol):
    """Update order book w/ simulated order.
    TODO: add support for consuming multiple orders.

    :pair: currency pair (str)
        'btc_cad', 'eth_cad', etc
    :section: book section (str)
        'bids' or 'asks'
    """
    values = g.db['sim_books'].find_one({'ex':ex, 'pair':pair})[section]
    values[0][1] -= abs(vol)
    log.debug('simbook.update, section=%s, vol=%s', section, values[0][1])
    g.db['sim_books'].update_one(
        {'ex':ex, 'pair':pair},
        {'$set':{section:values}}
    )

#-------------------------------------------------------------------------------
def merge(ex, pair, bids, asks):
    """Merge real order books w/ simulated books.

    :orders: sorted order book (dict).
        {'bids':[], 'asks':[]}
    """
    n_matches = 0
    orders = {'asks':asks, 'bids':bids}
    merged = {'asks':[], 'bids':[]}

    sim_book = g.db['sim_books'].find_one({'ex':ex, 'pair':pair})

    if sim_book is None:
        g.db['sim_books'].insert_one({'ex':ex, 'pair':pair, 'bids':bids, 'asks':asks})
        return

    # pair_name is defined ('trade','base')
    # but ask/bids are defined ('base', 'trade')

    for k in orders:
        for order in orders[k]:
            b_match = False
            for sim_order in sim_book[k]:
                # If price match, take lowest of the 2 volumes.
                if sim_order[0] == order[0]:
                    merged[k].append([order[0], min(order[1], sim_order[1])])
                    #log.debug('simbooks.merge match, price=%s, vol=%s',
                    #    order[0], min(order[1],sim_order[1]))
                    b_match = True
                    n_matches += 1
                    break
            if b_match == False:
                merged[k].append([order[0], order[1]])

    r = g.db['sim_books'].update_one(
        {'ex':ex, 'pair':pair},
        {'$set':{
            'ex':ex,
            'pair':pair,
            'bids':merged['bids'],
            'asks':merged['asks'],
        }},
        True
    )

    #log.debug('books.merge: %s modified orders syncd to new order_books', n_matches)
    #log.debug(new_orders)
