# app.main.endpoints

from bson.json_util import dumps
import logging, pprint
from flask import g
log = logging.getLogger(__name__)
from . import main # Blueprint

@main.route('/tickers/get', methods=['POST'])
def _tickers_get():

    from .quadrigacx import update_orderbooks
    update_orderbooks()
    return 'ok'

#-------------------------------------------------------------------------------
@main.route('/data/get', methods=['POST'])
def _data_get():

    tickers = g.db['ticker'].find_one(
        {"source" : "Canadian Bitcoin Index"})
    books = g.db['books'].find_one(
        {'book.name':'btc_cad', 'exchange':'QuadrigaCX'})

    for i in range(len(tickers['exchanges'])):
        exch = tickers['exchanges'][i]
        if exch['name'] == 'QuadrigaCX':
            exch['orders'] = books
            break

    return dumps(tickers)
