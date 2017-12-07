from datetime import datetime, timedelta
from bson import ObjectId
from pprint import pprint
from dateutil.parser import parse
import pymongo
import pandas as pd
from pandas import DataFrame
from pandas.io.json import json_normalize

pd.set_option('display.width',1000)
client = pymongo.MongoClient()
db = client['simbot']
ex = 'QuadrigaCX'
pair = ['btc','cad']

book_docs = list(
    db['pub_books'].find({'pair':['btc','cad']}).sort('date',-1).limit(25)
)
t1_data = book_docs[1]
t0_data = book_docs[5]
#------------------------------------------------------------------------------

_timer = datetime.utcnow()
results = {'df_askacts':None, 'df_bidacts':None, 'df_buys':None, 'df_sells':None}

trades = json_normalize(list(
    db['pub_trades'].find(
        {'pair':['btc','cad'], 'date':{'$gte':t0_data['date'], '$lte':t1_data['date']}},
        {'_id':0, 'volume':1, 'side':1, 'price':1, 'date':1, 'tid':1})
))

for side in ['bids', 'asks']:
    df_t0 = pd.DataFrame(data=[n for n in t0_data[side]],
        columns=['price_t0','volume_t0'])
    df_t1 = pd.DataFrame(data=[n for n in t1_data[side]],
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
    df_acts['date'] = df_acts['date'].fillna(value=t0_data['date'])
    df_acts = df_acts[['date', 'page', 'price', 'vdiff']]
    df_acts['action'] = ['ADD' if vdiff > 0 else 'CANCEL' for vdiff in df_acts['vdiff']]
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
    print(r)
    print('--------------------------------------')

print('\nCOMPLETED IN %s MS' %((datetime.utcnow() - _timer).microseconds/1000))
print('N_TOTAL_TRADES=%s' % len(trades))
#print('%s.PARSED ORDER FILLS, %s ACTUAL TRADES' %(
#    side.upper(), len(df_sells) + len(df_buys), len(df_trades)))
#print(df_trades.sort_values('date'))
#print('--------------------------------------')
