import logging
from flask import g, request
log = logging.getLogger(__name__)
from . import main

def simulate():

    log.info('hey hey!')

    return 'ok'
