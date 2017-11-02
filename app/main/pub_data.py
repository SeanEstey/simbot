# pub_data.py
import logging
from time import sleep
from datetime import datetime
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

            for trade in client.get_public_trades(time='minute', book=book):
                _doc = {
                    'ex':conf['NAME'],
                    'date':datetime.fromtimestamp(int(trade['date'])+(3600*6)),
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

            log.debug('%s/%s new trades, ex=%s, book=%s', n_new, n_total, 'QuadrigaCX', book)

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
            dt = datetime.fromtimestamp(int(orders['timestamp'])+(3600*6))

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

            g.db['pub_books'].insert_one(document)
            smart_emit('updateGraphData', dumps({'orderbook':document}))

#---------------------------------------------------------------
def book_diff(ex, pair, ordersv1, dt1, ordersv2, dt2, side):
    from pymongo import InsertOne
    from pymongo.errors import BulkWriteError

    _ordersv1= {}
    requests = []
    n_trades = 0

    # Build dict {'price':'volume'} from ordersv1
    for order in ordersv1:
        _ordersv1[order[0]] = order[1]

    # Now loop through ordersv2 bids/asks and lookup price key
    for order in ordersv2:
        prev = _ordersv1.get(order[0],None)

        # No change
        if prev and prev == order[1]:
            del _ordersv1[order[0]]
            continue
        # Volume change
        elif prev and prev != order[1]:
            requests.append(InsertOne({
                'ex':ex,
                'pair':pair,
                'side':side,
                'date':datetime.utcnow(),
                'action':'adjusted',
                'price':order[0],
                'volume':round((order[1] - prev),8),
                'remaining':round(order[1],8)
            }))
            n_trades += 1

            # TODO: See if the vol adjustment matches any
            # recorded trades in this timespan

            del _ordersv1[order[0]]
        # New order
        elif prev is None:
            requests.append(InsertOne({
                'ex':ex,
                'pair':pair,
                'side':side,
                'date':datetime.utcnow(),
                'action':'added',
                'price':order[0],
                'volume':round(order[1],8)
            }))

    # Any remaining orders in _ordersv1 were removed by maker
    for k in _ordersv1:
        requests.append(InsertOne({
            'ex':ex,
            'pair':pair,
            'side':side,
            'date':datetime.utcnow(),
            'action':'cancelled',
            'price':k,
            'volume':round(_ordersv1[k],8)
        }))

    # Test if n_trades matches number of already recorded trades with this
    # ex/pair in timespan between both orderbook snapshots
    qside = 'buy' if side == 'asks' else 'sell'

    trades = g.db['pub_trades'].find(
        {'ex':ex, 'pair':pair, 'date':{'$gte':dt1, '$lt':dt2}, 'side':qside}
    )

    print('book_diff(): pair=%s, side=%s, n_orderbook_changes=%s, n_trades=%s, n_actual_trades=%s'%(
        pair, side, len(requests), n_trades, trades.count()))

    if len(requests) > 0:
        g.db['pub_actions'].bulk_write(requests)
