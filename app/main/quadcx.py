# app.main.quadcx
import json
import requests
from datetime import datetime
from pprint import pprint
from logging import getLogger
from flask import g
from app.lib.timer import Timer
from app.main import ex_confs
from . import simbooks
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def update_ticker(pair):
    """Ticker JSON dict w/ keys: ['last','high','low','vwap','volume','bid','ask']
    """
    conf = ex_confs(name='QuadrigaCX')
    t1 = Timer()
    try:
        r = requests.get(conf['TICKER_URL'] % conf['PAIRS'][pair]['book'])
        data = json.loads(r.text)
    except Exception as e:
        log.exception('Quadriga ticker error: %s', str(e))
        raise

    for k in data:
        data[k] = float(data[k])
    data.update({'ex':'QuadrigaCX','pair':pair,'date':datetime.utcnow()})

    r = g.db['pub_tickers'].update_one(
        {'ex':'QuadrigaCX', 'pair':pair},
        {'$set':data},
        True # upsert
    )
