# app.main.tasks
import json, logging
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)
from app.main.bot import SimBot
from app.main import quadcx, coinsquare

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update(self, **rest):
    coinsquare.update()
    quadcx.update('btc_cad')

    gary = SimBot('Gary')
    n_sells = gary.eval_bids()
    balance = gary.balance()
    log.info('Gary update: sells=%s, CAD=$%s, BTC=%s',
        n_sells, round(balance['cad'],2), round(balance['btc'],5))
