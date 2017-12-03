from celery.schedules import crontab

imports = ('app.tasks', 'app.main.tasks')
broker_url = 'amqp://'
accept_content = ['json']
task_serializer = 'json'
result_serializer = 'json'
timezone = 'Canada/Mountain'
task_time_limit = 300
worker_concurrency = 1
beat_schedule = {
    'update_ex_data': {
        'task':'app.main.tasks.update_ex_data',
        'schedule': 15.0
    },
    'update_bots': {
        'task':'app.main.tasks.update_bots',
        'schedule': 15.0
    },
    'update_client_indicators': {
        'task':'app.main.tasks.update_client_indicators',
        'schedule': 600.0
    },
    'backup_mongo': {
        'task': 'app.main.tasks.backup_mongo',
        'schedule': crontab(hour=1, minute=0, day_of_week='*')
    }
}

