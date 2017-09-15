'''app.main.__init__'''
from flask import Blueprint

main = Blueprint(
    'main',
    __name__,
    static_folder='static',
    static_url_path='/static/main',
    template_folder='templates')

from . import views
