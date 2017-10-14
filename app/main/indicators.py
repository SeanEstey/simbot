# indicators.py
from bson.json_util import dumps
from datetime import datetime
from flask import g
from app.lib.timer import Timer
from logging import getLogger
log = getLogger(__name__)

#---------------------------------------------------------------
def analyze_order_book(orders):
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

    g.db['pub_books'].insert_one({
        'ex':'QuadrigaCX',
        'book':book,
        'date':datetime.utcnow(),
        'summary':summary,
        'bids':orders['bids'],
        'asks':orders['asks'],

        # Static book analysis
        'analysis': {
            'v_bid':v_bid,
            'v_ask':v_ask,
            'v_ratio':round(v_bid/v_ask,2),
            'p_ask_sens':ask_delta[1], # Req order volume to move price up 1%
            'p_bid_sens':bid_delta[1] # Req order volume to move price down 1%
        }
    })

#---------------------------------------------------------------
def get_book_metrics(ex, book, metric, start, end):
    results = list(
        g.db['pub_books'].find({
            'ex':ex,
            'book':book,
            'date':{'$gte':start, '$lte':end}
        }).sort('date',1)
    )
    log.debug('book_metrics, ex=%s, book=%s, key=%s, start=%s, end=%s, count=%s',
        ex, book, metric, start, end, len(results))

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

    # TRADE ANALYSIS
    """
    elif metric == 'v_traded':
        for r in results:
            r['v_traded'] = 0
            for bid in r['bids']:
                r['v_traded'] += float(bid[1])
            for ask in r['asks']:
                r['v_traded'] += float(ask[1])
            del r['asks']
            del r['bids']
    elif metric == 'v_bought':
        for r in results:
            r['v_bought'] = 0
    """

    return dumps(results)
