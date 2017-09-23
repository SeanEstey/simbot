# app.main.tasks
import json, logging
from pprint import pprint
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)
from app.main.bot import SimBot
from app.main import quadcx, coinsquare

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update(self, **rest):

    # Update market data
    quadcx.update('CAD','BTC')
    quadcx.update('CAD','ETH')
    coinsquare.update('CAD','BTC')

    # Go Garybot!
    gary = SimBot('Gary')
    gary.eval_bids()
    gary.eval_asks()

    balance = gary.balance()
    stats = gary.stats()

    log.info('Garybot earnings=$%s', round(stats['earnings'],2))

    """, cad=$%s, btc=%s, buys=%s, sells=%s, ',
      round(stats['earnings'],2), round(balance['cad'],2), round(balance['btc'],5),
        stats['n_buy_orders'], stats['n_sell_orders'])
    """
