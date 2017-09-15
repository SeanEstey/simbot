# app.main.endpoints

import logging, pprint
log = logging.getLogger(__name__)
from . import main # Blueprint

#-------------------------------------------------------------------------------
@main.route('/endp/book/get', methods=['POST'])
def _enp_get_book():

    from .simulate import get_orderbook
    json_data = get_orderbook()
    return json_data
