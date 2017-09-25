'''detect'''
import os, requests, socket, sys, time
from flask import current_app, g
from os import environ as env
import eventlet, flask #,celery
from logging import getLogger
log = getLogger(__name__)

G = '\033[92m'
Y = '\033[93m'
ENDC = '\033[0m'

#-------------------------------------------------------------------------------
def startup_msg(app, show_celery=False):

    hostname = env['HOSTNAME']
    host = 'http://%s' %(env['IP'])
    domain = env.get('DOMAIN',env['IP'])
    debug = 'ON' if app.config['DEBUG'] else 'OFF'
    sbox = 'enabled' if env['SANDBOX'] == 'True' else 'disabled'
    ssl = env.get('SSL','disabled')
    evntlt_v = eventlet.__version__
    flsk_v = flask.__version__

    from app.lib.utils import mem_check
    mem = mem_check()
    active = mem['active']
    total = mem['total']
    free = mem['free']
    from app.lib.utils import os_desc

    msg=\
    "       .__       ___.           __    \n"\
    "  _____|__| _____\_ |__   _____/  |_  \n"\
    " /  ___/  |/     \| __ \ /  _ \   __\ \n"\
    " \___ \|  |  Y Y  \ \_\ (  <_> )  |   \n"\
    "/____  >__|__|_|  /___  /\____/|__|   \n"\
    "     \/         \/    \/              \n"
    msg +=\
    "   %s\n" % os_desc() +\
    "   mem: %s/%s\n" % (free,total) +\
    "   %s\n" % host +\
    "   flask v%s\n" % flsk_v +\
    "   debug mode %s\n" % debug

    print( msg + ENDC)
    mem = mem_check()

    if not show_celery:
        return False

    from app.tasks import celery as celery_app
    import celery

    insp = celery_app.control.inspect()
    while not insp.stats():
        time.sleep(1)

    stats = insp.stats()
    stats = stats[stats.keys()[0]]
    broker = stats['broker']
    trnsprt = broker['transport']

    n_workers = '%s' %(stats['pool']['max-concurrency'])
    str_brkr = '%s://%s:%s' %(trnsprt, broker['hostname'], broker['port'])
    beat = 'on' if env['BEAT'] == 'True' else 'off'
    clry_v = celery.__version__
    c_host = 'celery@simbot'
    regist = '%s regist' % len(insp.registered()[c_host])
    sched = '%s sched' % len(insp.scheduled()[c_host])

    celery_msg =\
    "%s-------------------------------- %scelery@simbot\n"      %(G,Y) +\
    "%s-------------------------------- %s%s\n"                %(G,G,str_brkr) +\
    "%s-------------------------------- %s[config]\n"          %(G,G) +\
    "%s-------------------------------- %s  > version: %s\n"   %(G,G,clry_v) +\
    "%s-------------------------------- %s  > workers: [%s]\n" %(G,G,n_workers) +\
    "%s-------------------------------- %s  > beat:    %s\n"   %(G,G,beat) +\
    "%s-------------------------------- %s  > tasks:   %s, %s\n"%(G,G,regist,sched) +\
    ""

    print(celery_msg + ENDC)
    mem = mem_check()

#-------------------------------------------------------------------------------
def set_environ(app):

    if not env.get('SANDBOX'):
        env['SANDBOX'] = 'False'

    env['HOSTNAME'] = hostname = socket.gethostname()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com",80))
    except Exception as e:
        log.error('socket error connecting to gmail (desc: %s)', str(e))
        env['IP'] = 'False'
    else:
        env['IP'] = ip = s.getsockname()[0]
        s.close()

    try:
        domain = socket.gethostbyaddr(ip)[0]
    except Exception as e:
        log.warning('no domain found for host ip %s', ip)
        env['TEST'] = 'True'
        env['DOMAIN'] = 'False'
        env['SSL'] = 'False'
        env['HTTP_HOST'] = 'http://' + ip
        return
