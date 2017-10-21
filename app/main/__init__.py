'''app.main.__init__'''
from flask import Blueprint
from config import EXCHANGES, PAIRS

main = Blueprint(
    'main',
    __name__,
    static_folder='static',
    static_url_path='/static/main',
    template_folder='templates')

def ex_confs(name=None, api_only=True):
    if name is not None:
        for exchange in EXCHANGES:
            if exchange['NAME'] == name:
                return exchange

    if api_only == True:
        return [n for n in EXCHANGES if n['API_ENABLED'] == True]
    else:
        return EXCHANGES

def pair_conf(pair):
    return PAIRS[pair]

from . import views
from . import endpoints
