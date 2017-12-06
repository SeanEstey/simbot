from datetime import datetime, timedelta
from bson import ObjectId
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

####### ob_book_diff ##########

book_docs = list(
    db['pub_books'].find({'pair':['btc','cad']}).sort('date',-1).limit(25)
)
book_b = book_docs[1]
book_a = book_docs[4]

for side in ['bids', 'asks']:
    df_a = pd.DataFrame(
        data=[[book_a['date']]+n for n in book_a[side]],
        columns=['date_a','price_a','volume_a'])
    df_b = pd.DataFrame(
        data=[[book_b['date']]+n for n in book_b[side]],
        columns=['date_b','price_b','volume_b'])

    dfm = df_a.merge(df_b, left_on='price_a', right_on='price_b', how='outer')
    dfm = dfm.loc[ dfm['volume_a'] != dfm['volume_b'] ]

    print('found %s %s ob diffs:' % (len(dfm), side))
    print(dfm)

    for index, row in dfm.iterrows():
        # A. (vol_a=Float and vol_b=NaN) == filled order

        # B. (vol_a=NaN and vol_b=Float) == added order

        # C. (vol_a=Float, vol_b=Float, vol_a != vol_b) == partial order fill

        pass
