# app.main.tasks
import json, logging
from app import celery
from app.lib.timer import Timer
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_books(self, **rest):

    from app.main import quadcx, cbix, coinbase

    #coinbase.ticker()
    cbix.ticker()
    quadcx.ticker()
    quadcx.order_books()


