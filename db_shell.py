from datetime import datetime, timedelta
import pymongo
import pandas as pd
from pandas import DataFrame
from pandas.io.json import json_normalize
from dateutil.parser import parse
client = pymongo.MongoClient()
db = client['simbot']
ex = 'QuadrigaCX'
pair = ['btc','cad']

####### analyze_ob ##########
end = parse("2017-12-03T18:15:48.000Z")
start = end + timedelta(minutes=-10)
df = json_normalize(list(db['pub_trades'].find({
    'ex':ex, 'pair':pair, 'date':{'$gte':start, '$lte':end}
})))

df_buy = df.loc[ df['side'] == 'buy' ]
df_sell = df.loc[ df['side'] == 'sell' ]

results = {
    'n_buys': int(df_buy.count()['_id']),
    'buy_vol': round(float(df_buy['volume'].sum()), 5),
    'n_sells': int(df_sell.count()['_id']),
    'sell_vol': round(float(df_sell['volume'].sum()), 5),
    'price': round(float(df['price'].mean()), 2),
    'price_diff': round(float(df.iloc[-1]['price'] - df.iloc[0]['price']), 2),
}

results['buy_rate'] = round(float(results['n_buys'] / df.count()['_id']), 5)
results['vol_diff'] = round(float(results['buy_vol'] - results['sell_vol']), 5)
