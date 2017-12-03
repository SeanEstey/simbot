import pymongo
import pandas as pd
from pandas import DataFrame
from pandas.io.json import json_normalize

client = pymongo.MongoClient()
db = client['simbot']


datapoints = list(db['chart_series'].find({}))
df = json_normalize(datapoints)

