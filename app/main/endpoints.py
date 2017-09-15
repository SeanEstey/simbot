# app.main.test_endpoints

import logging
from flask import g, request
log = logging.getLogger(__name__)
from . import main

@main.route('/test_test', methods=['GET'])
def _test_wipe_sessions():

    return 'ok'
