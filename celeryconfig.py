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
    'update_books': {
        'task':'app.main.tasks.update_books',
        'schedule': crontab(minute='*/5')
    }
}
