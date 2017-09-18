# app.main.tasks
import json, logging
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_bots(self, **rest):
    from app.main import simbot
    simbot.update()
    simbot.summary()
