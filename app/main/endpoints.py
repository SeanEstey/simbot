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

@sio_server.on('initGraphData')
def init_graph():
    db = current_app.db_client['simbot']
    query = {'ex':'QuadrigaCX', 'pair':('btc','cad')}
    smart_emit('updateGraphData', dumps({
        'trades': list(db['pub_trades'].find(query).sort('date',-1).limit(500)),
        'orderbook': list(db['pub_books'].find(query).sort('date',-1).limit(1))[0]
    }))

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

@main.route('/test/indicators', methods=['GET'])
def _test_indicators():
    from datetime import datetime, timedelta
    from app.main.indicators import build_series

    utcnow = datetime.utcnow()#+timedelta(hours=6)
    build_series(
        'QuadrigaCX',
        ('btc','cad'),
        utcnow - timedelta(days=0, hours=4),
        utcnow)
    return 'OK'



