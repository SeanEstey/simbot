# tickers.py
from flask import g

def summary(ex, pair):
    return g.db['pub_tickers'].find_one({'ex':ex, 'pair':pair})
