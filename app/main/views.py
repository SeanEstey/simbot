# app.main.views

import logging, pprint
from flask import g, render_template, redirect, url_for
log = logging.getLogger(__name__)
from . import main # Blueprint

#-------------------------------------------------------------------------------
@main.route('/index')
def index():
    return render_template('base.html')

#-------------------------------------------------------------------------------
@main.errorhandler(404)
def err(e):
    log.info('rendering views/404.html')
    return render_template('404.html')

#-------------------------------------------------------------------------------
@main.route('/book')
def order_book():

    return render_template('book.html')

