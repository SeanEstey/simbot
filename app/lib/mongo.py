'''app.lib.mongo'''
import logging
import os
import pymongo
import db_auth
import config

#-------------------------------------------------------------------------------
def create_client(host=None, port=None, connect=True, auth=True):

    print 'CREATING MONGOCLIENT. PID %s' % os.getpid()

    client = pymongo.MongoClient(
        host = host or config.MONGO_URL,
        port = port or config.MONGO_PORT,
        tz_aware = True,
        connect = connect)

    if auth:
        authenticate(client)

    return client

#-------------------------------------------------------------------------------
def authenticate(client, user=None, pw=None):

    try:
        client.admin.authenticate(
            user or db_auth.user,
            pw or db_auth.password,
            mechanism='SCRAM-SHA-1')
    except Exception as e:
        print 'Mongo authentication error: %s' % str(e)
        raise

    #print 'MongoClient authenticated'
