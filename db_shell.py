from datetime import datetime, timedelta
from flask import g, current_app
from bson import ObjectId
from pprint import pprint
from dateutil.parser import parse
import pymongo
import pandas as pd
from pandas import DataFrame
from pandas.io.json import json_normalize

ctx = current_app.test_request_context()
ctx.push()
current_app.preprocess_request()

pd.set_option('display.width',1000)
client = pymongo.MongoClient()
db = client['simbot']
ex = 'QuadrigaCX'
pair = ['btc','cad']

#------------------------------------------------------------------------------
from app.main.pub_data import book_diff_df
book_docs = list(
    db['pub_books'].find({'pair':['btc','cad']}).sort('date',-1).limit(25)
)
t1_data = book_docs[1]
t0_data = book_docs[5]
_timer = datetime.utcnow()
last = list(g.db['pub_books'].find(
    {'ex':'QuadrigaCX', 'pair':['btc','cad']
}).sort('date',-1).limit(75))
r = book_diff_df(
    'QuadrigaCX',
    ('btc','cad'),
    last[35],
    last[5]
)
