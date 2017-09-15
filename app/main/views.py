# app.main.views

import logging
from flask import g, render_template, redirect, url_for
log = logging.getLogger(__name__)
from . import main # Blueprint

#-------------------------------------------------------------------------------
@main.route('/index')
def index():

    from .simulate import start_sim
    start_sim()
    return render_template('base.html')

#-------------------------------------------------------------------------------
@main.errorhandler(404)
def err(e):
    log.info('rendering views/404.html')
    return render_template('404.html')
