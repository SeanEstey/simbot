import logging
from flask import g, request
log = logging.getLogger(__name__)
from . import main

def start_sim():

    from app.main.tasks import task_exec_trade
    task_exec_trade.delay()
    log.info('Task run')
    return 'ok'
