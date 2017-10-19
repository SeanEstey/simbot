# indicators.py
from datetime import datetime, time, timedelta
from dateutil.parser import parse
from flask import g
from logging import getLogger
log = getLogger(__name__)

#---------------------------------------------------------------
def update_time_series():
    """Time series is for client chart data.
    """
    utcnow = datetime.now()+timedelta(hours=6)
    build_series(
        'QuadrigaCX',
        'btc_cad',
        utcnow - timedelta(days=1),
        utcnow)

#---------------------------------------------------------------
def build_series(ex, book, start, end):
    """Calculate key indicators for 10 min periods in given date range
    for given exchange/book.
    """
    p_start = p_end = datetime.combine(start.date(), time(start.hour, int(start.minute/10*10)))
    p_end += timedelta(minutes=10)
    n_mod = n_upsert = 0

    while p_start <= end:
        order_ind = from_orders(ex, book, p_start, p_end)
        trade_ind = from_trades(ex, book, p_start, p_end)

        r = g.db['chart_series'].update_one(
            {'ex':ex,'book':book,'start':p_start,'end':p_end},
            {'$set':{
                'avg.price': round(trade_ind.get('price',0.0),2),
                'avg.bid_price':round(order_ind.get('bid_price',0.0),2),
                'avg.bid_vol':round(order_ind['bid_vol'],5),
                'avg.bid_inertia':round(order_ind.get('bid_inertia',0.0),5),
                'avg.ask_price':round(order_ind.get('ask_price',0.0),2),
                'avg.ask_vol':round(order_ind.get('ask_vol',0.0),5),
                'avg.ask_inertia':round(order_ind.get('ask_inertia',0.0),5),
                'sum.buy_vol':trade_ind['buy_vol'],
                'sum.sell_vol':trade_ind['sell_vol'],
                'sum.n_buys':trade_ind['n_buys'],
                'sum.n_sells':trade_ind['n_sells']
            }},
            True
        )
        p_start += timedelta(minutes=10)
        p_end += timedelta(minutes=10)
        n_mod += r.modified_count
        n_upsert += 1 if r.upserted_id else 0

    log.debug('indicators modified=%s, created=%s', n_mod, n_upsert)

#---------------------------------------------------------------
def from_trades(ex, book, start, end):
    ind = {
        'price':[],
        'buy_vol':0.0,
        'sell_vol':0.0,
        'n_buys':0,
        'n_sells':0,
        'buy_rate':0
    }
    trades = g.db['pub_trades'].find({
        'exchange':ex, 'currency':book[0:3], 'date':{'$gte':start, '$lt':end}
    })
    for t in trades:
        ind['price'].append(t['price'])
        if t.get('side','') == 'buy':
            ind['buy_vol'] += t['volume']
            ind['n_buys'] += 1
        elif t.get('side''') == 'sell':
            ind['sell_vol'] += t['volume']
            ind['n_sells'] += 1

    ind['price'] = sum(ind['price'])/len(ind['price']) if len(ind['price']) > 0 else 0.0
    ind['buy_rate'] = ind['n_buys']/(ind['n_buys']+ind['n_sells']) if ind['n_buys']+ind['n_sells'] > 0 else 0.0
    return ind

#---------------------------------------------------------------
def from_orders(ex, book, start=None, end=None):
    ind = {
        'bid_price':[],
        'bid_vol':[],
        'bid_inertia':[],
        'ask_price':[],
        'ask_vol':[],
        'ask_inertia':[]
    }

    if start is None and end is None:
        docs = g.db['pub_books'].find({'ex':ex, 'book':book}).sort('date',-1).limit(1)
    else:
        docs = g.db['pub_books'].find({'ex':ex, 'book':book, 'date':{'$gte':start, '$lt':end}})

    if docs.count() < 1:
        for k in ind:
            ind[k] = 0.0
        return ind

    for doc in docs:
        #log.debug('averaging n=%s order_books', docs.count())
        asks = doc['asks']
        bids = doc['bids']
        v_ask = v_bid = 0.0
        ask_delta = [float(asks[0][0]) * 1.01, None]
        bid_delta = [float(bids[0][0]) * 0.99, None]

        for b in bids:
            v_bid += float(b[1])
            if bid_delta[1] is None and float(b[0]) <= bid_delta[0]:
                bid_delta[1] = v_bid
        for a in asks:
            v_ask += float(a[1])
            if ask_delta[1] is None and float(a[0]) >= ask_delta[0]:
                ask_delta[1] = v_ask

        ind['bid_price'].append(float(bids[0][0]))
        ind['bid_vol'].append(v_bid)
        ind['bid_inertia'].append(bid_delta[1])
        ind['ask_price'].append(float(asks[0][0]))
        ind['ask_vol'].append(v_ask)
        ind['ask_inertia'].append(ask_delta[1])

    ind['bid_price'] = sum(ind['bid_price'])/len(ind['bid_price']) if len(ind['bid_price']) > 0 else 0.0
    ind['bid_vol'] = sum(ind['bid_vol'])/len(ind['bid_vol']) if len(ind['bid_vol']) > 0 else 0.0
    ind['bid_inertia'] = sum(ind['bid_inertia'])/len(ind['bid_inertia']) if len(ind['bid_inertia']) > 0 else 0.0
    ind['ask_price'] = sum(ind['ask_price'])/len(ind['ask_price']) if len(ind['ask_price']) > 0 else 0.0
    ind['ask_vol'] = sum(ind['ask_vol'])/len(ind['ask_vol']) if len(ind['ask_vol']) > 0 else 0.0
    ind['ask_inertia'] = sum(ind['ask_inertia'])/len(ind['ask_inertia']) if len(ind['ask_inertia']) > 0 else 0.0
    return ind





"""agg = g.db['pub_books'].aggregate([
    {'$match':{'ex':ex, 'book':book, 'date':{'$gte':first,'$lt':p_end}}},
    {'$unwind':'$asks'},
    {'$group':{
        '_id':'$_id',
        'ask0':{'$first':{'$arrayElemAt':['$asks',0]}},
        'bid0':{'$first':{'$arrayElemAt':['$bids',0]}}
    }},
    {'$group':{
        '_id':'',
        'avg_ask':{'$avg':'$ask0'}, 'avg_bid':{'$avg':'$bid0'}}
    }
])
aggr = g.db['pub_trades'].aggregate([
    {'$match': {
        'exchange':ex,
        'currency':book[0:3],
        'date':{'$gte':start, '$lte':end}
    }},
    {'$group':{'_id':'$side', 'count':{'$sum':1}, 'volume':{'$sum':'volume'}}}
])"""
