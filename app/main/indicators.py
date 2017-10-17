# indicators.py
from bson.json_util import dumps
from datetime import datetime
from flask import g
from app.lib.timer import Timer
from logging import getLogger
log = getLogger(__name__)

#---------------------------------------------------------------
def order_book(ex, book):
    orders = g.db['pub_books'].find({'ex':ex, 'book':book}).sort('date',-1).limit(1)
    if orders.count() < 1:
        return False
    orders = list(orders)[0]

    # Total order book volumes
    v_ask = v_bid = 0
    # Volume required to shift price by >= 1%
    ask_delta = [float(orders['asks'][0][0]) * 1.01, None]
    bid_delta = [float(orders['bids'][0][0]) * 0.99, None]

    for b in orders['bids']:
        v_bid += float(b[1])
        if bid_delta[1] is None and float(b[0]) <= bid_delta[0]:
            bid_delta[1] = v_bid

    for a in orders['asks']:
        v_ask += float(a[1])
        if ask_delta[1] is None and float(a[0]) >= ask_delta[0]:
            ask_delta[1] = v_ask

    return {
        'v_bid':v_bid,
        'v_ask':v_ask,
        'v_ratio':round(v_bid/v_ask,2),
        'ask_inertia':round(ask_delta[1],5),
        'bid_inertia':round(bid_delta[1],5)
    }

#---------------------------------------------------------------
def calc_trade_vol(ex, book, start, end):
    """Calculate buy/sell trade volume and n_buys/n_sells during time period.
    """
    aggr = g.db['pub_trades'].aggregate([
        {'$match': {
            'exchange':ex,
            'currency':book[0:3],
            'date':{'$gte':start, '$lte':end}
        }},
        {'$group':{'_id':'$side', 'count':{'$sum':1}, 'volume':{'$sum':'volume'}}}
    ])
    return dumps(list(aggr))

#---------------------------------------------------------------
def get_trade_metrics(ex, book, metric, start, end):
    t1 = Timer()
    results = list(
        g.db['pub_books'].find({
            'ex':ex,
            'book':book,
            'date':{'$gte':start, '$lte':end}
        }).sort('date',1)
    )

    if metric == 'v_bought' or metric == 'v_sold':
        for r in results:
            r['v_bought'] = r['analysis']['v_bought']
            r['v_sold'] = r['analysis']['v_sold']
            r['n_buys'] = r['analysis']['n_buys']
            r['n_sells'] = r['analysis']['n_sells']
            del r['asks']
            del r['bids']

    _json = dumps(results)
    log.debug('trade_metric=%s [%ss]', metric, t1.clock(t='s'))
    return _json

#---------------------------------------------------------------
def get_book_metrics(ex, book, metric, start, end):
    t1 = Timer()
    results = list(
        g.db['pub_books'].find({
            'ex':ex,
            'book':book,
            'date':{'$gte':start, '$lte':end}
        }).sort('date',1)
    )
    #log.debug('book_metrics, ex=%s, book=%s, key=%s, start=%s, end=%s, count=%s',
    #    ex, book, metric, start, end, len(results))

    if metric == 'v_ask':
        for r in results:
            r['v_ask'] = 0
            for ask in r['asks']:
                r['v_ask'] += float(ask[1])
            del r['asks']
            del r['bids']
    elif metric == 'v_bid':
        for r in results:
            r['v_bid'] = 0
            for bid in r['bids']:
                r['v_bid'] += float(bid[1])
            del r['asks']
            del r['bids']
    elif metric == 'bid':
        for r in results:
            r['bid'] = float(r['summary']['bid'])
            del r['asks']
            del r['bids']
    elif metric == 'ask':
        for r in results:
            r['ask'] = float(r['summary']['ask'])
            del r['asks']
            del r['bids']
    elif metric == 'ask_inertia':
        for r in results:
            r['ask_inertia'] = r['analysis']['ask_inertia']
            del r['asks']
            del r['bids']
    elif metric == 'bid_inertia':
        for r in results:
            r['bid_inertia'] = r['analysis']['bid_inertia']
            del r['asks']
            del r['bids']
    elif metric == 'buy_rate':
        for r in results:
            r['buy_rate'] = r['analysis']['buy_rate']
            del r['asks']
            del r['bids']

    _json = dumps(results)
    #log.debug('book_metric=%s [%s]', metric, t1.clock(t='ms'))
    return _json
