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

# Exchange/Bot Config
ACTIVE_SIM_BOT = 'Terry'
EXCHANGES = [
    {
        'NAME': 'Coinsquare',
        'API_EXISTS':False,
        'API_ENABLED':False,
        'PAIRS': {
            ('btc','cad'): {
                'name':'btc_cad',
                'book':'btc_cad',
                'fee': 0.002
            },
            ('eth','cad'): {
                'name':'eth_cad',
                'book':'eth_cad',
                'fee': 0.002
            }
        },
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
        'CLIENT_ID':64288,
        'API_EXISTS':True,
        'API_ENABLED':True,
        'PAIRS': {
            ('btc','cad'): {
                'name':'btc_cad',
                'book':'btc_cad',
                'fee': 0.005
            },
            ('eth','cad'): {
                'name':'eth_cad',
                'book':'eth_cad',
                'fee': 0.005
            }
        },
        'TICKER_URL': 'https://api.quadrigacx.com/v2/ticker?book=%s', # btc_cad, eth_cad
        'BOOK_URL': 'https://api.quadrigacx.com/v2/order_book?book=%s', # %s=book_name
        'FUND_FEE_INTERAC': 0.015,
        'FUND_FEE_WIRE': 0,
        'FUND_FEE_EFT': 0.025,
        'WITH_FEE_WIRE': 0,
        'WITH_FEE_EFT': 0,
        'WITH_FEE_INTERAC': 0.02,
        'TRADE_FEE': {
            'btc_cad': 0.005,
            'eth_cad': 0.005,
            'eth_btc': 0.002
        }
    },
    {
        'NAME':'Kraken',
        'API_EXISTS':True,
        'API_ENABLED':False,
        'PAIRS': {
            ('btc','cad'): {
                'name':'XXBTZCAD',
                'book':'XXBTZCAD'
            },
            ('eth','cad'): {
                'name':'XETHZCAD',
                'book':'XETHZCAD'
            }
        },
        'TICKER_URL': 'https://api.kraken.com/0/public/Ticker?pair=%s' # %s=book
    }
]

PAIRS = {
    ('btc','cad'): {
        'MAX_VOL': 0.15,
        'MIN_ARBIT_RATE': 50,
        'ASK_INERTIA':15
    },
    ('eth','cad'): {
        'MAX_VOL': 1.5,
        'MIN_ARBIT_RATE': 25
    }
}
SMS_ALERT_NUMBER = "+17808635715"
