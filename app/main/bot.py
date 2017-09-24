"""Class: SimBot
"""
import logging
from flask import g
from app.lib.timer import Timer
from bson import ObjectId as oid
log = logging.getLogger(__name__)

config = {
    'MAX_BUY':500,
    'MAX_SELL_VOLUME': 0.5
}

#-------------------------------------------------------------------------------
def get_tickers(exch=None, currency=None):
    query = {}
    if exch:
        query['name'] = exch
    if currency:
        query['book'] = '%s_cad' % currency.lower()
    return list(g.db['exchanges'].find(query))

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
        bot.add_holding(ticker['name'], ticker['trade'])

    log.info('Created %s bot w/ $%s balance', name, start_cad)


########################### Class: SimBot ##########################
class SimBot():
    """TODO: determine volatility, adjust buy/sell margins dynamically.
    High volatility == bigger margins, low volatility == lower margins
    """
    _id = None
    name = None
    start_balance = None
    rules = None

    #---------------------------------------------------------------
    def add_holding(self, exch, currency):
        """status values: 'pending', 'open', 'closed'
        """
        r = g.db['holdings'].insert_one({
            'bot_id':self._id,
            'exchange':exch,
            'currency':currency,
            'status':'pending',
            currency:0.00000,
            'cad':0.00,
            'trades':[]
        })
        return g.db['holdings'].find_one({'_id':oid(r.inserted_id)})

    #---------------------------------------------------------------
    def holdings(self, exch=None, currency=None, status=None):
        """status values: 'pending', 'open', 'closed'
        """
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        if currency:
            query['currency'] = currency
        return list(g.db['holdings'].find(query))

    #---------------------------------------------------------------
    def update_holding(self, _id, exch, status, currency, vol, cad, trades):
        """status values: 'pending', 'open', 'closed'
        """
        g.db['holdings'].update_one(
            {'_id':_id},
            {'$set': {
                'status':status,
                currency:vol,
                'cad':cad,
                'trades':trades
            }})

    #---------------------------------------------------------------
    def buy_order(self, exch, holding, ask, ask_vol, options='market'):
        # TODO: handle eating through > 1 orders, proper fees
        FEE = 0.995
        MAX = 500.00
        currency = holding['currency']
        buy_value = round(min(ask*ask_vol, MAX),2)
        buy_vol = round(buy_value/ask,5)
        holding['trades'].append({
            'type':'BUY',
            'price':ask,
            'volume':buy_vol,
            'value':buy_value
        })
        self.update_holding(holding['_id'],
            exch, 'open', currency,
            holding[currency] + buy_vol,
            holding['cad'] - buy_value*FEE,
            holding['trades']
        )

        log.info('BUY order, exch=%s, %s=%s, cad=%s @ %s',
            exch, currency, buy_vol, buy_value, ask)
        return True

    #---------------------------------------------------------------
    def sell_order(self, exch, holding, bid, bid_vol, options='market'):
        # TODO: handle eating through > 1 orders, proper fees
        FEE=0.995
        MAX_VOL=0.5
        currency = holding['currency']
        sell_vol = min(holding[currency], bid_vol, MAX_VOL)
        sell_value = round(bid*sell_vol, 2)
        holding[currency] -= sell_vol
        holding['cad'] += sell_value*FEE
        status = 'open' if holding[currency] > 0 else 'closed'
        holding['trades'].append({
            'type':'SELL',
            'price':bid,
            'volume':sell_vol,
            'value':sell_value
        })
        self.update_holding(holding['_id'],
            exch, status, currency, holding[currency], holding['cad'], holding['trades'])

        log.info('SELL order, exch=%s, %s=%s, cad=%s @ %s',
            exch, currency, sell_vol, sell_value, bid)
        return True

    #---------------------------------------------------------------
    def eval_bids(self):
        """Evaluate each open holding, sell on margin criteria
        """
        n_sells=0
        _holdings = self.holdings(status='open')
        log.debug('---Evaluating SELL options for %s open holdings---', len(_holdings))

        for i in range(len(_holdings)):
            holding = _holdings[i]
            ticker = get_tickers(exch=holding['exchange'], currency=holding['currency'])[0]
            bid = ticker['bids'][0]
            margin = round(bid['price'] - holding['trades'][0]['price'],2)

            if margin >= self.rules['sell_margin']:
                self.sell_order(ticker['name'], holding, bid['price'], bid['volume'])
                n_sells+=1

            log.debug('holding #%s, exch=%s, p=%s, bid=%s, m=%s',
                i+1, holding['exchange'], holding['trades'][0]['price'], bid['price'], margin)
        log.debug('---%s SELLS made for %s holdings---', n_sells, len(_holdings))

    #---------------------------------------------------------------
    def eval_asks(self):
        log.debug('evaluating buy options (asks)...')
        n_buys = 0
        for ticker in get_tickers():
            BUY = False
            ask = ticker['asks'][0]
            holdings = self.holdings(exch=ticker['name'], currency=ticker['trade'])

            if len(holdings) == 0:
                BUY = True
            else:
                # Get recent holding BUY price. Buy order if ask price fallen below margin
                recent_trade = holdings[-1]['trades'][0]
                buy_margin = round(ask['price'] - recent_trade['price'],2)
                log.debug('exch=%s, last_buy=%s, ask={p:%s, v:%s}, m=%s',
                    ticker['name'], recent_trade['price'], ask['price'], round(ask['volume'],5), buy_margin)
                if buy_margin <= self.rules['buy_margin']:
                    BUY = True

            if BUY:
                new_holding = self.add_holding(ticker['name'], ticker['trade'])
                r = self.buy_order(ticker['name'], new_holding, ask['price'], ask['volume'])
                n_buys+=1
        return n_buys

    #---------------------------------------------------------------
    def balance(self, exch=None, status=None):
        """Returns dict: {'cad':float, 'btc':float}
        """
        query = {'bot_id':self._id}

        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status

        balance = g.db['holdings'].aggregate([
            {'$match':query},
            {'$group':{
                '_id':'', 'cad':{'$sum':'$cad'}, 'btc':{'$sum':'$btc'}, 'eth':{'$sum':'$eth'}}},
            {'$project':{'_id':0, 'cad':1, 'btc':1, 'eth':1}}
        ])
        return list(balance)[0]

    #---------------------------------------------------------------
    def stats(self, exch=None):
        op_bal = self.balance(status='open')
        cl_bal = self.balance(status='closed')
        btc_val = op_bal['btc'] * get_tickers(currency='btc')[0]['bid']
        eth_val = op_bal['eth'] * get_tickers(currency='eth')[0]['bid']
        net = (btc_val + eth_val + op_bal['cad'] + cl_bal['cad']) - self.start_balance
        earn = cl_bal['cad']
        n_open = len(self.holdings(status='open'))
        n_closed = len(self.holdings(status='closed'))

        return {
            'n_open': n_open,
            'n_closed': n_closed,
            'cad': cl_bal['cad'],
            'btc': op_bal['btc'],
            'eth': op_bal['eth'],
            'btc_value': btc_val,
            'eth_value': eth_val,
            'earnings': earn,
            'net': op_bal['cad'] + earn + btc_val + eth_val
        }

    #---------------------------------------------------------------
    def eval_arbitrage(self):
        pass

    #---------------------------------------------------------------
    def calc_limit_imbalance(self, exch=None):
        """research paper: "as we found that on most days, large spreads
        indicated low price changes"""
        pass

        """r = g.db['trades'].find({
            'exchange':'QuadrigaCX',
            'currency':'btc',
            'date':{'$gte':ISODate("2017-09-23T16:50:41.000-06:00")}
        })
        """
    #---------------------------------------------------------------
    def __init__(self, name):
        """Load bot properties from Mongo
        """
        bot = g.db['bots'].find_one({'name':name})
        self._id = bot['_id']
        self.rules = bot['rules']
        self.start_balance = bot['start_balance']
        self.name = name
