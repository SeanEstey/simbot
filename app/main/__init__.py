'''app.main.__init__'''
from flask import Blueprint
from config import EXCHANGES, PAIRS

main = Blueprint(
    'main',
    __name__,
    static_folder='static',
    static_url_path='/static/main',
    template_folder='templates')

def exch_conf(name):
    for exchange in EXCHANGES:
        if exchange['NAME'] == name:
            return exchange

def pair_conf(name):
    for pair in PAIRS:
        if pair['NAME'] == name:
            return pair

from . import views
from . import endpoints
