'''run'''
import eventlet, os, time, sys, getopt
from os import environ, system
from flask import current_app, g, session
from app import create_app
app = create_app('app')

#-------------------------------------------------------------------------------
@app.before_request
def do_setup():
    session.permanent = True
    g.db = current_app.db_client['simbot']
    g.group = 'sean'

#-------------------------------------------------------------------------------
@app.after_request
def do_teardown(response):
    return response

#-------------------------------------------------------------------------------
def main(argv):

    from detect import startup_msg
    from detect import set_environ
    import workers

    try:
        opts, args = getopt.getopt(argv,"bcd", ['beat', 'celery', 'debug'])
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt in('-b', '--beat'):
            environ['BEAT'] = 'True'
        if opt in('-c', '--celery'):
            environ['CELERY'] = 'True'
        elif opt in ('-d', '--debug'):
            app.config['DEBUG'] = True
            app.config['USE_DEBUGGER'] = True

    app.logger.debug('Starting server...')

    set_environ(app)
    workers.kill()
    time.sleep(1)
    if bool(environ.get('CELERY',False)):
        workers.start(beat=bool(environ.get('BEAT',False)))
    time.sleep(1)
    startup_msg(app, show_celery=False)

    app.logger.info("Server ready @%s", app.config['LOCAL_URL'])
    app.run(host='127.0.0.1', port=8000, debug=app.config['DEBUG'])

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
