"""Class: SimBot
"""
import logging
from flask import g
from app.lib.timer import Timer
from bson import ObjectId as oid
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
def get_tickers(exch=None):
    return [g.db['exchanges'].find_one({'name':exch})] if exch else list(g.db['exchanges'].find())

#-------------------------------------------------------------------------------
def create(name, start_cad, buy_margin, sell_margin):
    tickers = get_tickers()

    g.db['bots'].insert_one({
        'name':name,
        'start_balance': start_cad,
        'rules': {
            'buy_margin': buy_margin,
            'sell_margin': sell_margin
        }})

    bot = SimBot(name)

    for ticker in tickers:
        bot.add_holding(ticker['name'], round(start_cad/len(tickers),2))

    log.info('Created %s bot w/ $%s balance', name, start_cad)


########################### Class: SimBot ##########################
class SimBot():
    _id = None
    name = None
    start_balance = None
    rules = None

    #---------------------------------------------------------------
    def add_holding(self, exch, cad):
        g.db['holdings'].insert_one({
            'bot_id':self._id,
            'exchange':exch,
            'status':'pending',
            'btc_volume':0.00000,
            'cad_balance':cad,
            'trades':[]
        })

    #---------------------------------------------------------------
    def holdings(self, exch=None, status=None):
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        return list(g.db['holdings'].find(query))

    #---------------------------------------------------------------
    def update_holding(self, exch, status, btc_vol, cad_bal, trades):
        g.db['holdings'].update_one(
            {'bot_id':self._id, 'exchange':exch},
            {'$set': {
                'status':status,
                'btc_volume':btc_vol,
                'cad_balance':cad_bal,
                'trades':trades
            }})

    #---------------------------------------------------------------
    def buy_order(self, exch, price, volume, cost):
        # TODO: balance check
        # TODO: handle eating through > 1 orders

        holding = self.holdings(exch=exch)[0]
        print(holding)

        holding['trades'].append({
            'type':'BUY',
            'price':price,
            'volume':volume,
            'value':cost
        })

        self.update_holding(
            exch,
            'open',
            holding['btc_volume'] + volume,
            holding['cad_balance'] - cost,
            holding['trades']
        )

    #---------------------------------------------------------------
    def sell_order(self, exch, price, volume):

        pass

    #---------------------------------------------------------------
    def balance(self, exch=None):
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
            # Evaluate selling margins for each open holding
            _holdings = self.holdings(exch=ticker['name'], status='open')

            log.debug('%s open holdings on %s', len(_holdings), ticker['name'])

            for holding in _holdings:
                # Get price diff from initial BUY
                margin = ticker['bid'] - holding['trades'][0]['price']

                if margin > self.rules['sell_margin']:
                    log.debug('Sell margin=%s, bid_vol=%s, hold_vol=%s',
                        margin, ticker['volume'], holding['btc_volume'])

                    result = 'MAKE_SELL_ORDER'
                else:
                    log.debug('Sell margin=%s. Too low', margin)

    #---------------------------------------------------------------
    def eval_asks(self):
        for ticker in get_tickers():
            # Examine our earnings position. If poor, only buy on fall
            # in 24hr market price
            #log.debug('%s 24hr market change:%s', ticker['name'], ticker['price_24hour'])

            if 'GOOD_BUY_OPPORTUNITY':
                # Balance check
                _balance = self.balance(exch=ticker['name'])
                ask = ticker['ask']

                log.debug('Ask=%s, ask_vol=%s, cad_bal=%s',
                    ask, ticker['volume'], _balance['cad'])

                result = 'MAKE_BUY_ORDER'

    #---------------------------------------------------------------
    def eval_arbitrage(self):
        pass

    #---------------------------------------------------------------
    def __init__(self, name):
        """Load bot properties from Mongo
        """
        bot = g.db['bots'].find_one({'name':name})
        self._id = bot['_id']
        self.rules = bot['rules']
        self.start_balance = bot['start_balance']
        self.name = name
