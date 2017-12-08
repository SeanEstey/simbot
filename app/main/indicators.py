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

    # TODO: pass the ndays/nhours args to build_series
    # if present, otherwise default is just minutes=10
    build_series(
        'QuadrigaCX',
        ('btc','cad'),
        datetime.utcnow() - timedelta(minutes=10),
        datetime.utcnow()
    )

#---------------------------------------------------------------
def build_series(ex, pair, start, end):
    """Calculate key indicators for 10 min periods in given date range
    for given exchange/book.
    """
    T_PERIOD = 10 # minutes

    m = round(start.minute, -1)
    if m == 60:
        m = 50
    p_start = p_end = datetime.combine(start.date(), time(start.hour, m))
    p_end += timedelta(minutes=T_PERIOD)
    n_mod = n_upsert = 0

    while p_start <= end:
        query = {'ex':ex,'pair':pair,'start':p_start,'end':p_end}
        log.debug('series, start=%s, end=%s, p_start=%s, p_end=%s',
            start, end, p_start, p_end)

        ob_ind = analyze_ob(ex, pair, p_start, p_end)
        ob_act_ind =  analyze_ob_actions(ex, pair, p_start, p_end)
        trade_ind = analyze_trades(ex, pair, p_start, p_end)

        r = g.db['chart_series'].update_one(query,
            {'$set':{
                'avg.bid_price': ob_ind.get('mean_bid',0.0),
                'avg.ask_price': ob_ind.get('mean_ask',0.0),
                'avg.bid_vol': ob_ind['sum_bid_vol'],
                'avg.ask_vol': ob_ind.get('sum_ask_vol',0.0),
                'avg.bid_inertia':ob_ind.get('mean_bid_inertia'),
                'avg.ask_inertia':ob_ind.get('mean_ask_inertia'),
                'avg.price': trade_ind.get('price',None),
                'sum.n_buys':trade_ind.get('n_buys',None),
                'sum.n_sells':trade_ind.get('n_sells',None),
                'sum.buy_vol':trade_ind.get('buy_vol',None),
                'sum.sell_vol':trade_ind.get('sell_vol',None),
                'orderbook': ob_ind
            }},
            True)

        g.db['indicators'].update_one(query,
            {'$set': {
                'orderbook': ob_ind,
                'ob_actions': ob_act_ind,
                'trades':trade_ind
            }},
            True)

        p_start += timedelta(minutes=T_PERIOD)
        p_end += timedelta(minutes=T_PERIOD)
        n_mod += r.modified_count
        n_upsert += 1 if r.upserted_id else 0
    log.debug('indicators modified=%s, created=%s', n_mod, n_upsert)

#---------------------------------------------------------------
def analyze_trades(ex, pair, start, end):
    """Analyze recorded trades.
    """
    df = json_normalize(list(g.db['pub_trades'].find({
        'ex':ex, 'pair':pair, 'date':{'$gte':start, '$lte':end}
    })))

    if df.empty:
        return {}

    df_buy = df.loc[ df['side'] == 'buy' ]
    df_sell = df.loc[ df['side'] == 'sell' ]

    return {
        'n_buys': int(df_buy.count()['_id']),
        'n_sells': int(df_sell.count()['_id']),
        'buy_vol': round(float(df_buy['volume'].sum()), 5),
        'sell_vol': round(float(df_sell['volume'].sum()), 5),
        'vol_diff': round(float(df_buy['volume'].sum() - df_sell['volume'].sum()), 5),
        'price': round(float(df['price'].mean()), 2),
        'price_diff': round(float(df.iloc[-1]['price'] - df.iloc[0]['price']), 2),
        'buy_rate': round(float(df_buy.count()['_id'] / df.count()['_id']), 5)
    }

#---------------------------------------------------------------
def analyze_ob(ex, pair, start=None, end=None):
    """Find indicators from examining structure of orderbooks.
    """
    df = json_normalize(list(g.db['pub_books'].find({
        'ex':ex, 'pair':pair, 'date':{'$gte':start, '$lte':end}
    })))

    #log.debug('analyze_ob, start=%s, end=%s, df.count=%s',
    #    start, end, df.count())

    df['ask_price'] = [ row[0][0] for row in df['asks'] ]
    df['ask_vol'] = [ row[0][1] for row in df['asks'] ]
    df['bid_price'] = [ row[0][0] for row in df['bids'] ]
    df['bid_vol'] = [ row[0][1] for row in df['bids'] ]

    ask_inertias = []
    bid_inertias = []
    bid_cutoff_price = float(df['bid_price'][0] * 0.99)
    ask_cutoff_price = float(df['ask_price'][0] * 1.01)

    for index, row in df.iterrows():
        rem_asks = [ n[1] for n in row['asks'] if n[0] <= ask_cutoff_price ]
        ask_inertias.append(sum(rem_asks)) if len(rem_asks) > 0 else False

        rem_bids = [ n[1] for n in row['bids'] if n[0] >= bid_cutoff_price ]
        bid_inertias.append(sum(rem_bids)) if len(rem_bids) > 0 else False

    df['ask_inertias'] = ask_inertias
    df['bid_inertias'] = bid_inertias

    return {
        'mean_ask': round(float(df['ask_price'].mean()), 2),
        'mean_bid': round(float(df['bid_price'].mean()), 2),
        'sum_ask_vol': round(float(df['ask_vol'].sum()), 5),
        'sum_bid_vol': round(float(df['bid_vol'].sum()), 5),
        'vol_spread': round(float(df['bid_vol'].sum() - df['ask_vol'].sum()), 5),
        'mean_ask_inertia': round(float(df['ask_inertias'].mean()), 5),
        'mean_bid_inertia': round(float(df['bid_inertias'].mean()), 5),
    }

#---------------------------------------------------------------
def analyze_ob_actions(ex, pair, start=None, end=None):
    """Analyze the maker orderbook actions--create, cancel, execute--already parsed out
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
    return results
