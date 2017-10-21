# Flask
TEMPLATES_AUTO_RELOAD = True
SECRET_KEY = 'secret'
TITLE = 'Trade Simulator'
DEBUG = False
LOG_PATH = '/root/simbot/logs/'
MONGO_URL = 'localhost'
MONGO_PORT = 27017
LOCAL_PORT = 8000
LOCAL_URL = 'http://localhost:%s' % LOCAL_PORT
PUB_PORT = 80
DB = 'simbot'
APP_ROOT_LOGGER_NAME = 'app'
CELERY_ROOT_LOGGER_NAME = 'app'
ENV_VARS = [
    'SANDBOX',
    'BEAT',
    'HTTP_HOST',
    'TEST'
]
SMS_ALERT_NUMBER = "+17808635715"
EXCHANGES = [
    {
        'NAME': 'Coinsquare',
        'API_EXISTS':False,
        'API_ENABLED':False,
        'BOOK_URL': 'https://coinsquare.io/api/v1/data/bookandsales/%s/%s/16?', #base,trade
        'FUND_FEE_BANK_DRAFT': 0.0025,
        'FUND_FEE_WIRE': 0.005,
        'WITH_FEE_BANK_DEPOSIT': 0.01,
        'WITH_FEE_WIRE': 0.005,
        'TRADE_FEE': {
            'btc_cad': 0.002, # Maker == 0.001
            'eth_cad': 0.002, # Maker == 0.001
            'eth_btc': 0.002  # Maker == 0.001
        }
    },
    {
        'NAME':'QuadrigaCX',
        'API_EXISTS':True,
        'API_ENABLED':True,
        'TICKER_URL': 'https://api.quadrigacx.com/v2/ticker?book=%s', # %s=book_name
        'BOOK_URL': 'https://api.quadrigacx.com/v2/order_book?book=%s', # %s=book_name
        'FUND_FEE_INTERAC': 0.015,
        'FUND_FEE_WIRE': 0,
        'FUND_FEE_EFT': 0.025,
        'WITH_FEE_WIRE': 0,
        'WITH_FEE_EFT': 0,
        'WITH_FEE_INTERAC': 0.02,
        'ASSETS':['btc', 'eth', 'cad'],
        'TRADE_FEE': {
            'btc_cad': 0.005,
            'eth_cad': 0.005,
            'eth_btc': 0.002
        }
    }
]
PAIRS = [
    {
        'NAME': 'btc_cad',
        'MAX_VOL': 0.15,
        'MIN_ARBIT_RATE': 50
    },
    {
        'NAME': 'eth_cad',
        'MAX_VOL': 1.5,
        'MIN_ARBIT_RATE': 25
    },
    {
        'NAME': 'eth_btc',
        'MAX_VOL': 1.25,
        'MIN_ARBIT_RATE': 0.0015
    }
]

