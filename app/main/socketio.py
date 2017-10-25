# app.main.socketio
from flask import g, current_app, has_app_context
from flask_socketio import SocketIO, emit
from logging import getLogger
log = getLogger(__name__)

# Main server initialized with flask app in run.py
sio_server = SocketIO()

# Client that uses message_queue to send emit signals to
# server. Can be used by celery tasks.
sio_client = SocketIO(message_queue='amqp://')

import eventlet
eventlet.monkey_patch()

#-------------------------------------------------------------------------------
def smart_emit(event, data, room=None):
    """Sends a socketio emit signal to the appropriate client (room).
    Can be called from celery task if part of a request (will be cancelled
    otherwise).
    """
    if room:
        sio_client.emit(event, data, room=room)
    else:
        sio_client.emit(event, data)

#-------------------------------------------------------------------------------
@sio_server.on_error()
def _on_error(e):
    log.error('socketio error=%s', str(e))

#-------------------------------------------------------------------------------
@sio_server.on('connect')
def sio_connect():
    pass

#-------------------------------------------------------------------------------
@sio_server.on('disconnect')
def sio_disconnect():
    pass

#-------------------------------------------------------------------------------
def dump():
    from flask import request
    from app.lib.utils import obj_vars
    log.debug('sio_server: \n%s', obj_vars(sio_server))
    log.debug('sio_server dir:\n%s', dir(sio_server))
    log.debug('sio_server.server: \n%s', obj_vars(sio_server.server))
    log.debug('sio_server.server dir:\n%s', dir(sio_server.server))
    log.debug('request:\n%s', obj_vars(request))
