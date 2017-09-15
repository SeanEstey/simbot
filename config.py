from datetime import timedelta

# Flask
TEMPLATES_AUTO_RELOAD = True
SESSION_COLLECTION = 'sessions'
SECRET_KEY = 'secret'

# App
TITLE = 'Trade Simulator'
DEBUG = False
SSL_CERT_PATH = None
LOG_PATH = '/root/simbot/logs/'
MONGO_URL = 'localhost'
MONGO_PORT = 27017
LOCAL_PORT = 8000
LOCAL_URL = 'http://localhost:%s' % LOCAL_PORT
PUB_PORT = 80
DB = 'simbot'
APP_ROOT_LOGGER_NAME = 'app'
CELERY_ROOT_LOGGER_NAME = 'app'

# Other
ENV_VARS = [
    'SANDBOX',
    'BEAT',
    'HTTP_HOST',
    'TEST']
