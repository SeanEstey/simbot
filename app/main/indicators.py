# indicators.py
from datetime import datetime, time, timedelta
from dateutil.parser import parse
import numpy
import pandas as pd
from pandas import DataFrame
from pandas.io.json import json_normalize
from flask import g
from logging import getLogger
log = getLogger(__name__)

#---------------------------------------------------------------
def update_time_series(ndays=None, nhours=None):
    """Time series is for client chart data.
    """
    utcnow = datetime.utcnow() #+timedelta(hours=6)
    build_series(
        'QuadrigaCX',
        ('btc','cad'),
        utcnow - timedelta(days=ndays or 0, hours=nhours or 1),
        utcnow)

#---------------------------------------------------------------
def build_series(ex, pair, start, end):
    """Calculate key indicators for 10 min periods in given date range
    for given exchange/book.
    """
    m = round(start.minute, -1)
    if m == 60:
        m = 50
    p_start = p_end = datetime.combine(start.date(), time(start.hour, m))
    p_end += timedelta(minutes=10)
    n_mod = n_upsert = 0

    # Calculate indicators for each 10 min period.
    while p_start <= end:
        book_ind = analyze_ob(ex, pair, p_start, p_end)
        trade_ind = analyze_trades(ex, pair, p_start, p_end)

        r = g.db['chart_series'].update_one(
            {'ex':ex,'pair':pair,'start':p_start,'end':p_end},
            {'$set':{
                'avg.bid_price': book_ind.get('bid_price',0.0),
                'avg.bid_vol': book_ind['bid_vol'],
                'avg.bid_inertia':book_ind.get('bid_inertia'),
                'avg.ask_inertia':book_ind.get('ask_inertia'),
                'avg.ask_price': book_ind.get('ask_price',0.0),
                'avg.ask_vol': book_ind.get('ask_vol',0.0),
                'avg.price': trade_ind['price'],
                'sum.n_buys':trade_ind['n_buys'],
                'sum.n_sells':trade_ind['n_sells'],
                'sum.buy_vol':trade_ind['buy_vol'],
                'sum.sell_vol':trade_ind['sell_vol'],
                'sum.net_vol':trade_ind['buy_vol'] - trade_ind['sell_vol'],
                'ob_action_indicators':analyze_ob_actions(ex, pair, p_start, p_end),
                'trade_indicators':trade_ind
            }},
            True
        )
        p_start += timedelta(minutes=10)
        p_end += timedelta(minutes=10)
        n_mod += r.modified_count
        n_upsert += 1 if r.upserted_id else 0

    log.debug('indicators modified=%s, created=%s', n_mod, n_upsert)

#---------------------------------------------------------------
def analyze_trades(ex, pair, start, end):
    ind = {
        'price':[],
        'buy_vol':0.0,
        'sell_vol':0.0,
        'n_buys':0,
        'n_sells':0,
        'buy_rate':0
    }
    trades = g.db['pub_trades'].find({
        'ex':ex, 'pair':pair, 'date':{'$gte':start, '$lt':end}
    })
    for t in trades:
        ind['price'].append(t['price'])
        if t.get('side','') == 'buy':
            ind['buy_vol'] += t['volume']
            ind['n_buys'] += 1
        elif t.get('side''') == 'sell':
            ind['sell_vol'] += t['volume']
            ind['n_sells'] += 1

    ind['price'] = round(sum(ind['price'])/len(ind['price']),2) if len(ind['price']) > 0 else 0.0
    ind['buy_rate'] = ind['n_buys']/(ind['n_buys']+ind['n_sells']) if ind['n_buys']+ind['n_sells'] > 0 else 0.0
    #log.debug(ind)
    return ind

#---------------------------------------------------------------
def analyze_ob(ex, pair, start=None, end=None):
    """Find indicators from examining structure of orderbooks.
    """

    if start is None and end is None:
        docs = g.db['pub_books'].find({'ex':ex, 'pair':pair}).sort('date',-1).limit(1)
    else:
        docs = g.db['pub_books'].find({'ex':ex, 'pair':pair, 'date':{'$gte':start, '$lt':end}})

    if docs.count() < 1:
        for k in ind:
            ind[k] = 0.0
        return ind

    # For each snapshot in series, find av determine indicators
    ask_prices = []
    bid_prices = []
    ask_vols = []
    bid_vols = []
    ask_inertias = []
    bid_inertias = []

    for doc in docs:
        asks = doc['asks']
        bids = doc['bids']

        # Price
        bid_prices.append(float(bids[0][0]))
        ask_prices.append(float(asks[0][0]))

        # Bid/Ask volume sums
        ask_vols.append(numpy.mean([float(n[1]) for n in asks]))
        bid_vols.append(numpy.mean([float(n[1]) for n in bids]))

        # Bid/Ask inertia: amount of order book volume needing to be executed
        # to move bid/ask price >= 1%. Lower values may predict sudden price swings.
        inertia = 0.0
        for b in bids:
            inertia += float(b[1])
            if float(b[0]) <= float(bids[0][0]) * 0.99:
                break
        bid_inertias.append(inertia)
        for a in asks:
            inertia += float(a[1])
            if float(a[0]) >= float(asks[0][0]) * 1.01:
                break
        ask_inertias.append(inertia)

    # Take average of all indicators.
    results = {
        'bid_price': round(sum(bid_prices)/len(bid_prices),2) if len(bid_prices) > 0 else 0.0,
        'ask_price': round(sum(ask_prices)/len(ask_prices),2) if len(ask_prices) > 0 else 0.0,
        'bid_vol': round(sum(bid_vols)/len(bid_vols),5) if len(bid_vols) > 0 else 0.0,
        'ask_vol': round(sum(ask_vols)/len(ask_vols),5) if len(ask_vols) > 0 else 0.0,
        'bid_inertia': round(sum(bid_inertias)/len(bid_inertias), 2) if len(bid_inertias) > 0 else 0.0,
        'ask_inertia': round(sum(ask_inertias)/len(ask_inertias), 2) if len(ask_inertias) > 0 else 0.0
    }

    #log.debug(results)
    return results

#---------------------------------------------------------------
def analyze_ob_actions(ex, pair, start=None, end=None):
    """Analyze the maker orderbook actions already parsed out
    in main.pub_data.book_diff().
    """
    df = json_normalize(list(g.db['pub_actions'].find({
        'ex':ex,
        'pair':pair,
        'date':{'$gte':start, '$lte':end}
    })))

    df1 = df.loc[ (df['side'] == 'bids') ]
    results = {
        'n_bids_added':  int(df1.loc[ df1['action'] == 'added' ].count()['_id']),
        'n_bids_removed': int(df1.loc[ df1['action'] == 'cancelled' ].count()['_id']),
        'n_bids_executed': int(df1.loc[ df1['action'] == 'trade' ].count()['_id']),
        'sum_bid_events': int(df1.count()['_id'])
    }

    df2 = df.loc[ (df['side'] == 'asks') ]
    results.update({
        'n_asks_added':  int(df2.loc[ df2['action'] == 'added' ].count()['_id']),
        'n_asks_removed': int(df2.loc[ df2['action'] == 'cancelled'].count()['_id']),
        'n_asks_executed': int(df2.loc[ df2['action'] == 'trade' ].count()['_id']),
        'sum_ask_events': int(df2.count()['_id'])
    })

    #log.debug(results)
    return results
