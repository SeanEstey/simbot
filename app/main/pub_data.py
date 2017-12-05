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
def book_diff_df(ex, pair, side, book_a, book_b):
    """Same as below but using pandas dataframes.
    https://stackoverflow.com/questions/28901683/pandas-get-rows-which-are-not-in-other-dataframe
    https://pandas.pydata.org/pandas-docs/stable/merging.html

    Algorithm:

    1. Build each orders list into pandas dataframe as: [price, date, volume]
    2. Add into frames list:
        frames=[df1, df2]
    3. Concat frames:
        pd.concat(frames)
    4. Filter out rows where volumes match
    5. We're left with just the differences
    6. For rows with different volumes, iterate through trades with matching
    timeframe/price, catalog them
    7. For rows with volume in Col1 but not Col2, mark as cancelled order
    8. For rows with volume in Col2 but not Col1, mark as added order
    """

    pd.set_option('display.width',1000)

    df_a = pd.DataFrame(
        data=[[book_a['date']]+n for n in book_a[side]],
        columns=['date_a','price','volume_a'])
    df_a.set_index('price')

    df_b = pd.DataFrame(
        data=[[book_b['date']]+n for n in book_b[side]],
        columns=['date_b','price','volume_b'])
    df_b.set_index('price')

    df_big =  pd.concat([df_a,df_b],axis=0)
    df_big.columns = ['price','date_a','date_b','volume_a','volume_b']
    df_big['price'] = df_big['index']
    print(df_big.price.unique())

    #df_merge = pd.merge(df_a, df_b, on='price')
    #print(df_merge)

    #df_all = pd.concat([df_a,df_b],axis=1)
    #print(df_all)

    #df_diff = df_all.loc[ df_all['volume_a'] != df_all['volume_b'] ]
    #print(df_diff)

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
