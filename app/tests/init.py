import json, logging, os
import celery.result
from datetime import datetime, date, time, timedelta
from flask import g, url_for
from app import create_app
from app.auth import load_user
from app.lib.mongo import create_client
db_client = create_client(connect=True, auth=True)

#-------------------------------------------------------------------------------
def init(self):
    self.app = create_app('app')
    #self.celery = init_celery(self.app)
    self.user_id = 'sestey@vecova.ca'
    self.client = self.app.test_client()
    self._ctx = self.app.test_request_context()
    self._ctx.push()
    g.db = self.db = self.app.db_client['bravo']


#-------------------------------------------------------------------------------
def update_db(db, collection, _id, kwargs):
    return db[collection].update_one({'_id':_id},{'$set':kwargs})

