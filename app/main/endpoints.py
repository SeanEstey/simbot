# app.main.endpoints
from datetime import datetime
from bson.json_util import dumps
import logging
from flask import g, request, current_app
from . import main
from .simbot import SimBot
from config import ACTIVE_SIM_BOT

log = logging.getLogger(__name__)

from app.main.socketio import sio_server, smart_emit

@sio_server.on('initGraphStream')
def init_graph():
    log.debug('initGraphStream!')
    db = current_app.db_client['simbot']

    smart_emit(
        'initGraphStream',
        dumps(list(
            db['pub_trades'].find({'ex':'QuadrigaCX', 'pair':('btc','cad')}
            ).sort('date',-1).limit(500))
        )
    )

@main.route('/books/get', methods=['POST'])
def get_books():
    get = request.form.get
    return dumps(
        list(
            g.db['pub_books'].find_one(
                {'ex':get('ex'), 'pair':(get('asset'),'cad')}
            ).sort('date',-1).limit(1)
        )[0]
    )

@main.route('/stats/get', methods=['POST'])
def get_earnings():
    return dumps(SimBot(ACTIVE_SIM_BOT).stats())

@main.route('/holdings/get', methods=['POST'])
def get_holdings():
    return dumps(SimBot(ACTIVE_SIM_BOT).holdings())

@main.route('/tickers/get', methods=['POST'])
def get_tickers():
    return dumps(list(g.db['pub_tickers'].find()))

@main.route('/trades/get', methods=['POST'])
def get_trades():
    get = request.form.get
    return dumps(list(
        g.db['pub_trades'].find({
            'ex':get('ex'),
            'pair':(get('asset'),'cad'),
            'date':{'$gte':datetime.fromtimestamp(int(get('since')))}
        }).sort('date',1)))

@main.route('/indicators/get', methods=['POST'])
def _get_ind():
    get = request.form.get
    return dumps(list(
        g.db['chart_series'].find({
            'ex':get('ex'),
            'pair':(get('asset'), 'cad'),
            'start':{'$gte':datetime.fromtimestamp(int(get('since')))}
        }).sort('start',1)))

@main.route('/books/update', methods=['POST'])
def _update_books():
    if get('exchange') == 'Coinsquare':
        coinsquare.update('CAD', 'BTC')
    return 'OK'
