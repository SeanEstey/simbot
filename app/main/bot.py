"""app.main.SimBot
"""
import logging
from app.lib.timer import Timer
from bson import ObjectId as oid
log = logging.getLogger(__name__)

# WRITEME
def get_ticker(exch=None):
    return g.db['tickers'].find({'name':exch}) if exch else g.db['tickers'].find()

#-------------------------------------------------------------------------------
class SimBot():

    _id = None
	name = None
    start_balance = None
    rules = None

    #---------------------------------------------------------------
    def get_holdings(self, exch=None, status=None):
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        return list(g.db['holdings'].find(query))

    #---------------------------------------------------------------
    def get_balance(self, exch=None):
        """Returns dict: {'cad':float, 'btc':float}
        """
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        balance = g.db['holdings'].aggregate([
            {'$match':query},
            {'$group':{'_id':'', 'cad':{'$sum':'$cad_balance'}, 'btc':{'$sum':'$btc_volume'}}}
        ])
        return list(balance)[0]

    #---------------------------------------------------------------
    def eval_bids(self):
        for ticker in get_tickers():
            holdings = self.get_holdings(exch=ticker['exchange'], status='open')

            log.debug('%s open holdings on %s', len(holdings), ticker['exchange')

            # Evaluate selling margins for each open holding
            for holding in holdings:
                buy_price = holding['trades'][0]['price']
                bid = ticker['bid']
                margin = bid - buy_price # round decimals?

                if margin > self.rules['sell_margin']:
                    log.debug('Sell margin=%s, bid_vol=%s, hold_vol=%s',
                        margin, ticker['volume'], holding['btc_volume'])

    #---------------------------------------------------------------
    def eval_asks(self):
        for ticker in get_tickers():
            balance = self.get_balance(exch=ticker['exchange'])

            # Examine our earnings position. If poor, only buy on fall
            # in 24hr market price

            ask = ticker['ask']
            log.debug('%s 24hr market change:%s', ticker['exchange'], ticker['price_24hour'])

            if 'GOOD_BUY_OPPORTUNITY':
                # Balance check
                log.debug('Ask=%s, ask_vol=%s, cad_bal=%s',
                    ask, ticker['volume'], balance['cad'])

                # Make buy order
                order = 'MAKE_BUY_ORDER'

    #---------------------------------------------------------------
    def __init__(self, name):
        """Load bot properties from Mongo
        """
        bot = g.db['bots'].find_one({'name':name})
        self._id = bot['_id']
        self.rules = bot['rules']
        self.start_balance = bot['start_balance']
        self.name = name


"""
closed_holdings = [
    {
        'bot_id': odi("949j9kdkkld93"),
        'exchange':'Coinsquare',
        'status':'closed',
        'btc_volume':0.00000,
        'cad_balance':685.00,
        'trades': [
            {'type':'BUY', 'price':4500.00, 'volume':0.15000, 'value':675.00},
            {'type':'SELL', 'price':4571.00, 'volume':0.15000, 'value':685.00}
        ]
    }
]
open_holdings = [
    {
        'bot_id': odi("949j9kdkkld93"),
        'exchange':'QuadrigaCX',
        'status':'open',
        'btc_volume':1.39930,
        'cad_balance':0,
        'trades': [
            {'type':'BUY', 'price':5000.00, 'volume':1.3993, 'value':6996.00}
        ]
    }
]
"""
