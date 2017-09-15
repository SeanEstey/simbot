# app.main.tasks

import json, logging
from datetime import datetime, date, time, timedelta as delta
from dateutil.parser import parse
from flask import current_app, g, request
from app import celery
from celery import states
from celery.exceptions import Ignore
from app.lib.timer import Timer
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def task_exec_trade(self, arg1=None, arg2=None, arg3=None, **rest):

    log.info('Executing trade as celery task')
