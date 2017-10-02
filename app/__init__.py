# app __init__
import logging, os
from flask import g, Flask
from celery import Celery

celery = Celery(__name__, broker='amqp://')
from app.uber_task import UberTask
celery.Task = UberTask

# CLASSES
class DebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG
class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO
class WarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.WARNING
class colors:
    BLUE = '\033[94m'
    GRN = '\033[92m'
    YLLW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[37m'
    ENDC = '\033[0m'
    HEADER = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#-------------------------------------------------------------------------------
def create_app(pkg_name, mongo_client=True):
    """Create Flask app/blueprints, setup DB and logging.
    """
    from werkzeug.contrib.fixers import ProxyFix
    from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
    from config import LOG_PATH as path
    import config

    app = Flask(pkg_name)
    app.config.from_object(config)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.jinja_env.add_extension("jinja2.ext.do")

    from app.lib import mongo
    app.db_client = mongo.create_client(auth=False)

    # Flask App Logger & Handlers
    app.logger.setLevel(DEBUG)
    app.logger.addHandler(file_handler(DEBUG,
        '%sdebug.log'%path,
        filtr=DEBUG,
        color=colors.WHITE))
    app.logger.addHandler(file_handler(INFO,
        '%sevents.log'%path,
        filtr=INFO,
        color=colors.GRN))
    app.logger.addHandler(file_handler(WARNING,
        '%sevents.log'%path,
        filtr=WARNING,
        color=colors.YLLW))
    app.logger.addHandler(file_handler(ERROR,
        '%sevents.log'%path,
        filtr=ERROR,
        color=colors.RED))

    # Blueprints
    from app.main import main as main_mod
    app.register_blueprint(main_mod)
    from app.quadriga import quadcx as quadcx_mod
    app.register_blueprint(quadcx_mod)
    return app

#-------------------------------------------------------------------------------
def get_key(name, k=None):
    """Return API key.

    :name: key name
    """
    conf = g.db['keys'].find_one({'name':name})

    if conf is None:
        log.exception('No key document found with name=%s', name)
        raise

    if k and k not in conf:
        log.exception('Subkey=%s not found in name=%s', k, name)
        raise

    return conf if not k else conf[k]

#---------------------------------------------------------------------------
def file_handler(level, file_path,
                 filtr=None, fmt=None, datefmt=None, color=None, name=None):

    from logging import DEBUG

    handler = logging.FileHandler(file_path)
    handler.setLevel(level)

    if name is not None:
        handler.name = name
    else:
        handler.name = 'lvl_%s_file_handler' % str(level or '')

    if filtr == logging.DEBUG:
        handler.addFilter(DebugFilter())
    elif filtr == logging.INFO:
        handler.addFilter(InfoFilter())
    elif filtr == logging.WARNING:
        handler.addFilter(WarningFilter())

    formatter = logging.Formatter(
        colors.BLUE + (fmt or '[%(asctime)s %(name)s]: ' + colors.ENDC + color + '%(message)s') + colors.ENDC,
        #(datefmt or '%m-%d %H:%M'))
        (datefmt or '%H:%M'))

    handler.setFormatter(formatter)
    return handler
