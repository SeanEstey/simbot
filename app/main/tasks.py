# app.main.tasks
import logging
from datetime import datetime, timedelta
from app import celery
from flask import g
from app.main import quadcx, coinsquare, indicators, pub_data
from app.main.simbot import SimBot
from app.main import simbooks
from app.main.socketio import smart_emit
from app.quadriga import QuadrigaClient
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_ex_data(self, **rest):
    """Save public trade/orderbook data, update simulation orderbooks. Called
    every 10 sec.
    """
    pub_data.save_tickers()
    pub_data.save_trades()
    pub_data.save_orderbook()
    simbooks.merge_all()

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_bots(self, **rest):
    """Make buy/sell decisions. Called every 30 sec.
    """
    bot = SimBot('Terry')
    bot.update()

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_time_series_indicators(self, **rest):
    """Update chart data. Called every 10 min.
    """
    indicators.update_time_series()
