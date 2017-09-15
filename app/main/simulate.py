# simulate.py

import json, logging
from pprint import pprint
from flask import g, request
import requests
log = logging.getLogger(__name__)
from . import main

#-------------------------------------------------------------------------------
def get_orderbook():

    r = requests.get("https://api.quadrigacx.com/v2/ticker?book=btc_cad")
    return r.text

#-------------------------------------------------------------------------------
def start_sim():

    from app.main.tasks import task_exec_trade
    task_exec_trade.delay()
    log.info('Task run')
    return 'ok'
