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
    'update_exchanges': {
        'task':'app.main.tasks.update_exchanges',
        'schedule': 60.0
    },
    'analyze_indicators': {
        'task':'app.main.tasks.analyze_indicators',
        'schedule': 60.0
    }
}
#'update_bots': {
#    'task':'app.main.tasks.update_bots',
#    'schedule': 30.0
#},
