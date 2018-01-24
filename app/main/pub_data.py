# pub_data.py
import logging
from time import sleep
from pprint import pprint
import pandas as pd
from pandas.io.json import json_normalize
from datetime import datetime
from pymongo import InsertOne
from pymongo.errors import BulkWriteError
from app import celery
from flask import g
from pymongo import ReturnDocument
from bson.json_util import dumps
from app.main import ex_confs
from app.main import quadcx
from app.main.socketio import smart_emit
from app.quadriga import QuadrigaClient
from config import ACTIVE_SIM_BOT
log = logging.getLogger(__name__)

#------------------------------------------------------------------------------
def save_tickers():
    quadcx.update_ticker(('btc','cad'))
    quadcx.update_ticker(('eth','cad'))

#------------------------------------------------------------------------------
def save_trades():
    """Trade document: {
        'ex': <str> exchange name,
        'date': <datetime> in UTC,
        'tid': <str> trade_id,
        'pair': <tuple> ('btc','cad') inserted as list ['btc','cad']
        'side': <str> buy/sell,
        'volume': <float>,
        'price': <float>
    }
    """
    for conf in ex_confs():
        api = g.db['sim_bots'].find_one({'name':ACTIVE_SIM_BOT})['api'][0]
        client = QuadrigaClient(
            api_key=api['key'],
            api_secret=api['secret'],
            client_id=conf['CLIENT_ID'])

        for pair in conf['PAIRS']:
            n_new = n_total = 0
            book = conf['PAIRS'][pair]['book']

            trades = client.get_public_trades(time='minute', book=book)

            if len(trades) == 0:
                continue

            trades.reverse()

            for trade in trades:
                _doc = {
                    'ex':conf['NAME'],
                    'date':datetime.utcfromtimestamp(int(trade['date'])),
                    'tid':trade['tid'],
                    'pair':pair,
                    'side':trade['side'].upper(),
                    'volume':round(float(trade['amount']),5),
                    'price':float(trade['price'])
                }
                result = g.db['pub_trades'].replace_one(
                    {'tid':trade['tid']},
                    _doc,
                    upsert=True)
                n_total += 1

                if result.upserted_id:
                    log.info('%s trade, ex=%s, pair=%s, price=%s, vol=%s',
                        trade['side'].upper(), _doc['ex'], pair, _doc['price'], _doc['volume'])
                    smart_emit('updateGraphData', dumps({'trades':[_doc]}))
                    n_new+=1
            #log.debug('%s/%s new trades, ex=%s, book=%s', n_new, n_total, 'QuadrigaCX', book)

#------------------------------------------------------------------------------
def save_orderbook():
    for conf in ex_confs():
        api = g.db['sim_bots'].find_one({'name':ACTIVE_SIM_BOT})['api'][0]
        client = QuadrigaClient(
            api_key=api['key'],
            api_secret=api['secret'],
            client_id=conf['CLIENT_ID'])

        for pair in conf['PAIRS']:
            orders = client.get_public_orders(book=conf['PAIRS'][pair]['book'])
            dt = orders['date'] = datetime.utcfromtimestamp(int(orders['timestamp']))

            for bids in orders['bids']:
                bids[0] = float(bids[0])
                bids[1] = float(bids[1])
            for asks in orders['asks']:
                asks[0] = float(asks[0])
                asks[1] = float(asks[1])

            last = g.db['pub_books'].find({'ex':conf['NAME'], 'pair':pair}
                ).sort('date',-1).limit(1)
            if last.count() > 0:
                last = list(last)[0]
                book_diff_df(conf['NAME'], pair, last, orders)

            document = {
                'ex':conf['NAME'],
                'pair':pair,
                'date':dt,
                'bids':orders['bids'],
                'asks':orders['asks']
            }

            # Capped collection, no need to manage the size
            g.db['pub_books'].insert_one(document)

            smart_emit('updateGraphData', dumps({'orderbook':document}))

#------------------------------------------------------------------------------
def book_diff_df(ex, pair, t0_data, t1_data):
    """Same as below but using pandas dataframes.
    t0_data, t1_data : db.pub_books documents with orderbook snapshots
    """
    _timer = datetime.utcnow()
    r = {'df_askacts':[], 'df_bidacts':[], 'df_buys':[], 'df_sells':[]}

    for side in ['bids', 'asks']:
        _type = 'SELL' if side == 'bids' else 'BUY'
        df1 = pd.DataFrame(
            data=[n for n in t0_data[side]],
            columns=['price_t0','volume_t0'])
        df2 = pd.DataFrame(
            data=[n for n in t1_data[side]],
            columns=['price_t1','volume_t1'])

        # Find price/volume diffs
        df3 = df1.merge(df2,
            left_on='price_t0', right_on='price_t1', how='outer')
        df3['price'] = df3.price_t0.combine_first(df3.price_t1)
        df3.sort_values('price')
        df3['position'] = df3.index
        df3['vdiff'] = df3['volume_t1'].subtract(
            df3['volume_t0'], fill_value=0)
        df3 = df3.loc[df3.vdiff != 0]
        df3.drop(
            ['price_t0','price_t1','volume_t1','volume_t0'],
            inplace=True, axis=1)

        # Build Trades dataframe
        dftd = json_normalize(list(
            g.db['pub_trades'].find({'ex':ex, 'pair':pair, 'side':_type,
                'date':{'$gte':t0_data['date'], '$lte':t1_data['date']}},
                {'_id':0, 'volume':1, 'side':1, 'price':1, 'date':1, 'tid':1})
        ))
        if not dftd.empty:
            dftd = pd.merge(df3, dftd, on='price', how='right' )
            dftd = dftd[
                ['date', 'position', 'tid', 'side', 'price', 'vdiff', 'volume']]
            dftd.drop(['vdiff'],inplace=True,axis=1)
            dftd['action'] = 'FILL'
            dftd['position'] = dftd['position'].fillna(-1)
            dftd.sort_index(inplace=True)

        # Filter out the trades, leaving only NEW & CANCEL actions
        if not dftd.empty:
            df_acts = df3.loc[~df3['price'].isin(dftd['price'])]
        else:
            df_acts = df3
        df_acts.reset_index(inplace=True)
        df_acts['date'] = t0_data['date']
        df_acts = df_acts[['date', 'position', 'price', 'vdiff']]
        df_acts['action'] = ['ADD' if vdiff > 0 else 'CANCEL' for vdiff in df_acts['vdiff']]

        if side == 'bids':
            r.update({'df_sells': dftd, 'df_bidacts': df_acts})
        elif side == 'asks':
            r.update({'df_buys': dftd,'df_askacts': df_acts})

    # Save to DB
    df_allacts = r['df_askacts'].append(r['df_bidacts'])
    df_alltrades = r['df_buys'].append(r['df_sells'])
    df_allacts['ex'] = df_alltrades['ex'] = ex
    list_allacts = df_allacts.to_dict('records')
    for n in range(0,len(list_allacts)):
        list_allacts[n]['pair'] = pair
    list_alltrades = df_alltrades.to_dict('records')
    for n in range(0,len(list_alltrades)):
        list_alltrades[n]['pair'] = pair
    if len(list_allacts) > 0:
        g.db['pub_actions_'].insert_many(list_allacts)
    if len(list_alltrades) > 0:
        g.db['pub_actions_'].insert_many(list_alltrades)

    # Print results to stdout
    """
    for k in ['df_askacts', 'df_bidacts', 'df_buys', 'df_sells']:
        print(k.upper())
        print(r[k])
        print('--------------------------------------')
    """
    elapsed = (datetime.utcnow()-_timer).microseconds/1000
    n_diffs = len(r['df_askacts']) + len(r['df_bidacts']) + len(r['df_buys']) + len(r['df_sells'])
    print('\nDURATION=%sms, OB.DIFFS=%s, TRADES.TOTAL=%s' %(
        (datetime.utcnow()-_timer).microseconds/1000, n_diffs,
        len(r['df_buys']) + len(r['df_sells'])))
