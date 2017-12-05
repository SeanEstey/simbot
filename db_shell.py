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

id_a = ObjectId("5a25db9e43d0c4562e496aa5") # 11:34, 50 asks
id_b = ObjectId("5a25dbe943d0c4562e496ae5") # 11:36, 49 asks
book_a = db['pub_books'].find_one({"_id":id_a})
book_b = db['pub_books'].find_one({"_id":id_b})
side = 'asks'

df_a = pd.DataFrame(
    data=[[book_a['date']]+n for n in book_a[side]],
    columns=['date_a','price','volume_a'])
df_a.set_index('price')

df_b = pd.DataFrame(
    data=[[book_b['date']]+n for n in book_b[side]],
    columns=['date_b','price','volume_b'])
df_b.set_index('price')

