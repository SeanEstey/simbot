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
    def buy_order(self, exch, holding, ask, ask_vol):
        # TODO: handle eating through > 1 orders, proper fees
        FEE = 0.995
        MAX = 500.00

        holding = self.holdings(exch=exch)[0]

        buy_value = min(holding['cad_balance'], ask*ask_vol, MAX)
        buy_volume = round(buy_value/ask,5)

        holding['trades'].append({
            'type':'BUY',
            'price':ask,
            'volume':buy_volume,
            'value':buy_value
        })
        self.update_holding(
            exch,
            'open',
            holding['btc_volume'] + buy_volume,
            holding['cad_balance'] - buy_value*FEE,
            holding['trades']
        )

        log.info('BUY order, exch=%s, volume=%s, cad=%s @ price=%s',
            exch, buy_volume, buy_value, ask)

        return True

    #---------------------------------------------------------------
    def sell_order(self, exch, holding, bid, bid_vol):
        # TODO: handle eating through > 1 orders, proper fees
        FEE=0.995
        MAX_VOL=0.5

        sell_vol = min(holding['btc_volume'], bid_vol, MAX_VOL)
        sell_value = round(bid*sell_vol, 2)
        holding['btc_volume'] -= sell_vol
        holding['cad_balance'] += sell_value*FEE
        status = 'open' if holding['btc_balance'] > 0 else 'closed'
        holding['trades'].append({
            'type':'SELL',
            'price':bid,
            'volume':sell_vol,
            'value':sell_value
        })
        self.update_holding(
            exch, status,
            holding['btc_volume'], holding['cad_balance'], holding['trades'])

        log.info('SELL order, exch=%s, volume=%s, cad=%s @ price=%s',
            exch, sell_vol, sell_value, bid)

        return True

    #---------------------------------------------------------------
    def balance(self, exch=None):
        """Returns dict: {'cad':float, 'btc':float}
        """
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        balance = g.db['holdings'].aggregate([
            {'$match':query},
            {'$group':{'_id':'', 'cad':{'$sum':'$cad_balance'}, 'btc':{'$sum':'$btc_volume'}}},
            {'$project':{'_id':0, 'cad':1, 'btc':1}}
        ])
        return list(balance)[0]

    #---------------------------------------------------------------
    def eval_bids(self):
        n_sells = 0

        for ticker in get_tickers():
            # Evaluate selling margins for each open holding
            _holdings = self.holdings(exch=ticker['name'], status='open')

            #log.debug('%s open holdings on %s', len(_holdings), ticker['name'])

            for holding in _holdings:
                # Get price diff from initial BUY
                bid = ticker['bids'][0]

                margin = round(bid['price'] - holding['trades'][0]['price'],2)

                if margin < self.rules['sell_margin']:
                    log.debug('Sell margin=%s. Too low', margin)
                    continue

                log.debug('Sell margin=%s, bid_vol=%s, hold_vol=%s',
                    margin, ticker['volume'], round(holding['btc_volume'],5))

                r = self.sell_order(ticker['name'], holding, bid['price'], bid['volume'])

                if r:
                    n_sells +=1

        return n_sells

    #---------------------------------------------------------------
    def eval_asks(self):
        n_buys = 0

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

                r = self.buy_order(
                    ticker['name'],
                    self.holding(exch=ticker['name']),
                    ask['price'],
                    ask['volume'])

                if r:
                    n_buys += 1

        return n_buys

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
