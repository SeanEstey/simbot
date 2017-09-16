# app.main.views

import logging, pprint
from flask import g, render_template, redirect, url_for
log = logging.getLogger(__name__)
from . import main # Blueprint

#-------------------------------------------------------------------------------
@main.route('/')
def index():
    return render_template('index.html')
