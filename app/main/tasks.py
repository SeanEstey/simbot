# app.main.tasks
import json, logging
from app import celery
from flask import g
from app.lib.timer import Timer
log = logging.getLogger(__name__)
from app.main import simbot

#-------------------------------------------------------------------------------
@celery.task(bind=True)
def update_bots(self, **rest):
    simbot.update()
    simbot.summary()
