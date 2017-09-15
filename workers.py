import eventlet, time, sys, getopt
from os import environ, system

#-------------------------------------------------------------------------------
def kill():
    '''Kill any existing worker/beat processes, start new worker
    '''

    system("ps aux | "\
           "grep '/usr/bin/python /usr/local/bin/celery' | "\
           "awk '{print $2}' |"\
           "sudo xargs kill -9")

    print 'Celery workers killed'

#-------------------------------------------------------------------------------
def start(beat=True):
    '''Start celery worker/beat as child processes.
    IMPORTANT: If started from outside app or with --detach option, will NOT
    have os.environ vars
    '''

    if not beat:
        environ['BRV_BEAT'] = 'False'
    else:
        print 'Starting celery beat daemon...'
        system('celery -A app.tasks.celery beat -f logs/celery_beat.log -l INFO &')

    print 'Starting celery workers...'
    system('celery -A app.tasks.celery -n simbot worker -f logs/celery_worker.log -Ofair &') # -l WARNING -Ofair &')

#-------------------------------------------------------------------------------
if __name__ == "__main__":

    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv,"skr", ['start', 'kill', 'restart'])
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-k', '--kill'):
            kill()
        elif opt in('-s', '--start'):
            start()
        elif opt in('-r', '--restart'):
            kill()
            time.sleep(1)
            start()
