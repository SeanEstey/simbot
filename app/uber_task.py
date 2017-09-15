'''app.uber_task'''
import os
from logging import getLogger
from celery import Task
from flask import g, has_app_context, has_request_context,\
make_response, request, current_app
from bson.objectid import ObjectId
from app.lib.timer import Timer

log = getLogger(__name__)

__all__ = ['UberTask']

class UberTask(Task):
    '''Preserves flask request and app contexts within the worker task.
    g.db: new DB client + connection
    '''

    REQ_KW = '_flask_request_context'
    USERID_KW = '_user_id_oid'
    ENVIRON_KW = '_environ_var'
    flsk_app = None
    db_client=None
    buf_mongo_hndlr = None
    user = None
    group = None
    timer = None

    #---------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        '''Called by worker
        '''

        req_ctx = has_request_context()
        app_ctx = has_app_context()
        call = lambda: super(UberTask, self).__call__(*args, **kwargs)
        context = kwargs.pop(self.REQ_KW, None)

        with self.flsk_app.app_context():
            if context:
                with self.flsk_app.test_request_context(**context):
                    self._load_context_vars(kwargs)
                    result = call()
                    self.flsk_app.process_response(make_response(result or ''))
                    return result
            else:
                with self.flsk_app.test_request_context():
                    self._load_context_vars(kwargs)
                    result = call()
                    self.flsk_app.process_response(make_response(''))
                    return result

        return result

    #---------------------------------------------------------------------------
    def apply(self, args=None, kwargs=None, **options):
        '''Called by Flask app
        '''

        #log.debug('apply args=%s, kwargs=%s, options=%s', args, kwargs, options)

        if options.pop('with_request_context', True) or has_app_context():
            self._push_contexts(kwargs)

        return super(UberTask, self).apply(args, kwargs, **options)

    #---------------------------------------------------------------------------
    def retry(self, args=None, kwargs=None, **options):
        '''Called by Flask app
        '''

        if options.pop('with_request_context', True) or has_app_context():
            self._push_contexts(kwargs)

        return super(UberTask, self).retry(args, kwargs, **options)

    #---------------------------------------------------------------------------
    def apply_async(self, args=None, kwargs=None, **rest):
        '''Called by Flask app. Wrapper for apply_async
        '''

        #log.debug('apply_async args=%s, kwargs=%s, rest=%s', args, kwargs, rest)

        if rest.pop('with_request_context', True) or has_app_context():
            self._push_contexts(kwargs)

        return super(UberTask, self).apply_async(args, kwargs, **rest)

    #---------------------------------------------------------------------------
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        '''Called by worker on task fail
        '''

        task_name = self.name.split('.')[-1]

        if self.group:
            with self.flsk_app.app_context():
                g.group = self.group
                log.exception('Task %s failed: %s.',
                    task_name, exc, extra={'trace':einfo.traceback})
        else:
            log.exception('Task %s failed: %s',
                task_name, exc, extra={'trace':einfo.traceback})

    #---------------------------------------------------------------------------
    def _push_contexts(self, kwargs):
        '''Pass flask request/app context + flask.g vars into kwargs for worker task.
        '''

        kwargs[self.ENVIRON_KW] = {}

        app = self.flsk_app if self.flsk_app else current_app
        for var in app.config['ENV_VARS']:
            kwargs[self.ENVIRON_KW][var] = os.environ.get(var, '')

        if not has_request_context():
            return

        # keys correspond to arguments of :meth:`Flask.test_request_context`
        context = {
            'path': request.path,
            'base_url': request.url_root,
            'method': request.method,
            'headers': dict(request.headers),
        }

        if '?' in request.url:
            context['query_string'] = request.url[(request.url.find('?') + 1):]

        kwargs[self.REQ_KW] = context

    #---------------------------------------------------------------------------
    def _load_context_vars(self, kwargs):
        '''Called by worker. Load any request/app context + flask.g vars saved
        by _push_contexts
        '''

        env_vars = kwargs.pop(self.ENVIRON_KW, None)

        if env_vars:
            for k in env_vars:
                os.environ[k] = env_vars[k]

        g.db = self.db_client['simbot']
        g.timer = Timer()
