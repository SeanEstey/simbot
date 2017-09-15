# app.main.views

import logging
from flask import g, render_template, redirect, url_for
log = logging.getLogger(__name__)
from . import main # Blueprint

#-------------------------------------------------------------------------------
@main.route('/')
def show_landing():
    log.info('rendering views/base.html')
    return render_template('base.html')

@main.errorhandler(404)
def page_not_found(e):
    log.info('rendering views/404.html')
    return render_template('404.html')
