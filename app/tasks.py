'''app.tasks'''
import logging, os
from flask import g
from celery.task.control import revoke
from celery.signals import task_prerun, task_postrun, task_failure, task_revoked
from celery.signals import worker_process_init, worker_ready, worker_shutdown
from celery.signals import celeryd_init, celeryd_after_setup
from app import create_app, celery
from app.lib.mongo import create_client, authenticate
from uber_task import UberTask
import celeryconfig

# Pre-fork vars
UberTask.flsk_app = app = create_app('app', kv_sess=False, mongo_client=False)
UberTask.db_client = parent_client = create_client(connect=False, auth=False)
celery.config_from_object(celeryconfig)
celery.Task = UberTask

@celeryd_init.connect
def _celeryd_init(**kwargs):
    print 'CELERYD_INIT'

@celeryd_after_setup.connect
def _celeryd_after_setup(sender, instance, **kwargs):
    print 'CELERYD_AFTER_SETUP'

@worker_ready.connect
def parent_ready(**kwargs):
    '''Called by parent worker process'''

    print 'WORKER_READY. PID %s' % os.getpid()

@worker_shutdown.connect
def parent_shutdown(**kwargs):

    print 'WORKER_SHUTTING_DOWN'

@worker_process_init.connect
def child_init(**kwargs):
    '''Called by each child worker process (forked)'''

    # Experimental
    global celery
    UberTask.db_client = child_client = create_client(auth=False)
    celery.Task = UberTask

    # Set root logger for this child process
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)

    print 'WORKER_CHILD_INIT. PID %s' % os.getpid()

@task_prerun.connect
def task_init(signal=None, sender=None, task_id=None, task=None, *args, **kwargs):
    '''Dispatched before a task is executed by Task obj. Sender == Task.
    @args, @kwargs: the tasks positional and keyword arguments'''

    print 'RECEIVED TASK %s' % sender.name.split('.')[-1]

@task_postrun.connect
def task_done(signal=None, sender=None, task_id=None, task=None, retval=None, state=None, *args, **kwargs):
    '''Dispatched after a task has been executed by Task obj.
    @Sender: the task object executed
    @task_id: Id of the task to be executed
    @task: The task being executed
    @args: The tasks positional arguments
    @kwargs: The tasks keyword arguments
    @retval: The return value of the task
    @state: Name of the resulting state'''

    task_name = sender.name.split('.')[-1]
    print 'COMPLETED TASK %s' % task_name

@task_failure.connect
def task_failed(signal=None, sender=None, task_id=None, exception=None, traceback=None, einfo=None, *args, **kwargs):

    pass
    """name = sender.name.split('.')[-1]
    print 'TASK_FAILURE. NAME %s' % name
    app.logger.error('Task %s failed. Click for more info.', name,
        extra={
            'exception': str(exception) if exception else None,
            'traceback': str(traceback) if traceback else None,
            'task_args': args,
            'task_kwargs': kwargs})
    """

@task_revoked.connect
def task_killed(sender=None, task_id=None, request=None, terminated=None, signum=None, expired=None, *args, **kwargs):
    '''Called by worker parent. Task is revoked and child worker is also
    terminated. A new child worker will spawn, causing Mongo fork warnings.'''

    from app.lib.utils import obj_vars

    str_req = obj_vars(request)
    name = sender.name.split('.')[-1]
    app.logger.warning('Task %s revoked', name, extra={'request':str_req})
    print 'TASK_REVOKED. NAME %s' % name
