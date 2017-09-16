# app.main.cbix
import json
import requests
from flask import g
from app.lib.timer import Timer
from logging import getLogger
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def ticker():
    """CBIX Ticker data from Canadian exchanges
    """

    from config import CBIX

    try:
        r = requests.get(CBIX['url'])
    except Exception as e:
        log.exception('Failed to get Quadriga ticker book: %s', str(e))
        raise
    else:
        data = json.loads(r.text)

    low = high = data['exchanges'][0]

    for i in range(len(data['exchanges'])):
        exch = data['exchanges'][i]
        exch.update({
            'ask':float(exch['ask']),
            'bid':float(exch['bid']),
            'last':float(exch['last'])
        })
        if exch['last'] > high['last']:
            high = exch
        elif exch['last'] < low['last']:
            low = exch

    data['spread'] = {
        'high':high['last'],
        'low':low['last'],
        'diff': high['last']-low['last']
    }

    r = g.db['ticker'].update_one(
        {'source':data['source']},
        {'$set':data},
        True
    )

    log.info('%s tickers updated, spread=%s',
        len(data['exchanges']), data['spread']['diff'])
