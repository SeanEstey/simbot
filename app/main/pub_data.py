# pub_data.py
import logging
from time import sleep
from pprint import pprint
import pandas as pd
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

#---------------------------------------------------------------
def save_tickers():
    quadcx.update_ticker(('btc','cad'))
    quadcx.update_ticker(('eth','cad'))

#---------------------------------------------------------------
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
                    'side':trade['side'],
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

#---------------------------------------------------------------
def save_orderbook():
    for conf in ex_confs():
        api = g.db['sim_bots'].find_one({'name':ACTIVE_SIM_BOT})['api'][0]
        client = QuadrigaClient(
            api_key=api['key'],
            api_secret=api['secret'],
            client_id=conf['CLIENT_ID'])

        for pair in conf['PAIRS']:
            orders = client.get_public_orders(book=conf['PAIRS'][pair]['book'])
            dt = datetime.utcfromtimestamp(int(orders['timestamp']))

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
                book_diff(conf['NAME'], pair, last['bids'], last['date'], orders['bids'], dt, 'bids')
                book_diff(conf['NAME'], pair, last['asks'], last['date'], orders['asks'], dt, 'asks')

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

#---------------------------------------------------------------
def book_diff_df(ex, pair, t0_data, t1_data):
    """Same as below but using pandas dataframes.
    t0_data, t1_data : documents from db.pub_books collection
    https://stackoverflow.com/questions/28901683/pandas-get-rows-which-are-not-in-other-dataframe
    https://pandas.pydata.org/pandas-docs/stable/merging.html
    """
    _timer = datetime.utcnow()
    results = {'df_askacts':None, 'df_bidacts':None, 'df_buys':None, 'df_sells':None}

    trades = json_normalize(list(
        db['pub_trades'].find(
            {'pair':['btc','cad'], 'date':{'$gte':t0_data['date'], '$lte':t1_data['date']}},
            {'_id':0, 'volume':1, 'side':1, 'price':1, 'date':1, 'tid':1})
    ))

    for side in ['bids', 'asks']:
        df_t0 = pd.DataFrame(
            data=[n for n in t0_data[side]],
            columns=['price_t0','volume_t0'])
        df_t1 = pd.DataFrame(
            data=[n for n in t1_data[side]],
            columns=['price_t1','volume_t1'])

        # Merge together along price index
        df_diff = df_t0.merge(df_t1,
            left_on='price_t0', right_on='price_t1', how='outer')
        df_diff['price'] = df_diff.price_t0.combine_first(df_diff.price_t1)
        df_diff.sort_values('price')
        df_diff['page'] = df_diff.index
        df_diff['vdiff'] = df_diff['volume_t1'].subtract(
            df_diff['volume_t0'],
            fill_value=0)

        # Filter out orders without any changes
        df_diff = df_diff.loc[df_diff.vdiff != 0]
        df_diff.drop(
            ['price_t0','price_t1','volume_t1','volume_t0'],
            inplace=True, axis=1)

        # Merge trades made during timespan along price index
        t_side = 'sell' if side == 'bids' else 'buy'
        df_diff = df_diff.merge(trades.loc[trades.side == t_side],
            left_on='price', right_on='price', how='outer')
        df_trades = df_diff.loc[df_diff.tid.notna()].copy()
        df_trades = df_trades[
            ['date', 'page', 'tid', 'side', 'price', 'vdiff', 'volume']]
        df_trades.index.name = '%s.TRADES' %(t_side.upper())

        df_acts = df_diff.loc[df_diff.tid.isna()].copy()
        df_acts['date'] = df_acts['date'].fillna(value=t0_data[0])
        df_acts = df_acts[['date', 'page', 'price', 'vdiff']]
        df_acts['action'] = ['added' if vdiff > 0 else 'cancelled' for vdiff in df_acts['vdiff']]
        df_acts.index.name = '%s.ACTIONS' %(side.upper())

        if side == 'bids':
            results.update({
                'df_sells': df_trades,
                'df_bidacts': df_acts
            })
        elif side == 'asks':
            results.update({
                'df_buys': df_trades,
                'df_askacts': df_acts
            })

    for k in ['df_askacts', 'df_bidacts', 'df_buys', 'df_sells']:
        r = results[k]
        print('LENGTH=%s'%(len(r)))
        print(r)
        print('--------------------------------------')

    print('\nCOMPLETED IN %s MS' %((datetime.utcnow() - _timer).microseconds/1000))
    print('N_TOTAL_TRADES=%s' % len(trades))
    #print('%s.PARSED ORDER FILLS, %s ACTUAL TRADES' %(
    #    side.upper(), len(df_sells) + len(df_buys), len(df_trades)))
    #print(df_trades.sort_values('date'))
    #print('--------------------------------------')

#---------------------------------------------------------------
def book_diff(ex, pair, ordersv1, dt1, ordersv2, dt2, side):
    """Given two separate orderbooks, each saved from a different moment in time,
    reconstruct the set or order actions between snapshots.(ADD, CANCEL, TRADE)
    """

    _ordersv1= {}
    requests = []

    # Test if n_trades matches number of already recorded trades with this
    # ex/pair in timespan between both orderbook snapshots
    qside = 'buy' if side == 'asks' else 'sell'
    trades = g.db['pub_trades'].find(
        {'ex':ex, 'pair':pair, 'date':{'$gte':dt1, '$lt':dt2}, 'side':qside}
    ).sort('date',1)
    trades = list(trades)
    n_trades_saved = 0

    # Build dict {'price':'volume'} from ordersv1
    for order in ordersv1:
        _ordersv1[order[0]] = order[1]

    # Now loop through ordersv2 bids/asks and lookup price key
    for order in ordersv2:
        # book_v1 order volume at given price
        v1_order_vol = _ordersv1.get(order[0],None)
        v2_order_vol = order[1]

        # No change
        if v1_order_vol and v1_order_vol == v2_order_vol:
            del _ordersv1[order[0]]
            continue
        # Volume change
        elif v1_order_vol and v1_order_vol != v2_order_vol:
            vol_remain = round(v1_order_vol,8)
            vol_filled = 0
            bMatch=False
            for trade in trades:
                if trade['price'] == order[0]:
                    vol_remain -= trade['volume']
                    vol_filled += trade['volume']
                    requests.append(InsertOne({
                        'ex':ex,
                        'pair':pair,
                        'side':side,
                        'date':trade['date'],
                        'action':'trade',
                        'price':trade['price'],
                        'tid':trade['tid'],
                        'volume':trade['volume']*-1,
                        'remaining':round(vol_remain,8)
                    }))
                    n_trades_saved += 1
                    bMatch=True

            if bMatch:
                # If entire order was filled by trades but positive volume
                # remains, final action must have been creation of new order
                # at same price.
                if vol_filled >= v1_order_vol and v2_order_vol > 0:
                    # Some volume was added to this order
                    requests.append(InsertOne({
                        'ex':ex,
                        'pair':pair,
                        'side':side,
                        'date':datetime.utcnow(),
                        'action':'added',
                        'price':order[0],
                        'volume':round(v2_order_vol,8)
                    }))
            # No trades found to explain vol diff across snapshots
            # Order must have been removed and remade at same vol and diff
            # price
            else:
                #log.debug('unknown order action(s), side=%s, p=%s, v1_vol=%s, v2_vol=%s',
                #    side, order[0], v1_order_vol, v2_order_vol)

                requests.append(InsertOne({
                    'ex':ex,
                    'pair':pair,
                    'side':side,
                    'date':datetime.utcnow(),
                    'action':'cancelled',
                    'price':order[0],
                    'volume':round(v1_order_vol,8)
                }))
                requests.append(InsertOne({
                    'ex':ex,
                    'pair':pair,
                    'side':side,
                    'date':datetime.utcnow(),
                    'action':'added',
                    'price':order[0],
                    'volume':round(v2_order_vol,8)
                }))

            del _ordersv1[order[0]]
        # New order
        elif v1_order_vol is None:
            requests.append(InsertOne({
                'ex':ex,
                'pair':pair,
                'side':side,
                'date':datetime.utcnow(),
                'action':'added',
                'price':order[0],
                'volume':round(order[1],8)
            }))

    # Any orders in book snapshot #1 but not #2 were either completed
    # trades or cancelled by maker
    for k in _ordersv1:
        vol_executed = 0.0
        bMatch=False
        for trade in trades:
            if trade['price'] == k:
                requests.append(InsertOne({
                    'ex':ex,
                    'pair':pair,
                    'side':side,
                    'date':trade['date'],
                    'action':'trade',
                    'price':trade['price'],
                    'tid':trade['tid'],
                    'volume':trade['volume']*-1,
                    'remaining':round(vol_executed,8)
                }))
                n_trades_saved += 1
                bMatch = True
                vol_executed += trade['volume']

        if not bMatch:
            requests.append(InsertOne({
                'ex':ex,
                'pair':pair,
                'side':side,
                'date':datetime.utcnow(),
                'action':'cancelled',
                'price':k,
                'volume':round(_ordersv1[k],8)
            }))

    # TODO: Check if any of the trades within the 2 snapshots happened so
    # quickly (order added + consumed) that they weren't captured in either of the orderbook snapshots
    if len(requests) > 0 and pair[0] == 'btc':
        log.debug('ob diff: pair=%s, side=%s, n_diffs=%s, n_trades=%s (%s)',
            pair, side, len(requests), n_trades_saved, len(trades))
        pprint(requests)

    if len(requests) > 0:
        g.db['pub_actions'].bulk_write(requests)
