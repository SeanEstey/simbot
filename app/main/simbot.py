"""Class: SimBot
"""
import logging
from flask import g, current_app
from app.main import ex_confs, pair_conf
from app.lib.timer import Timer
from bson import ObjectId as oid
from app.main.sms import compose
from app.main.socketio import smart_emit
from app.main import indicators, simbooks, simex
from config import PAIRS
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
def create(name, start_cad, buy_margin, sell_margin):
    r = g.db['sim_bots'].insert_one({
        'name':name,
        'start_balance': start_cad,
        'rules': {
            'buy_margin': buy_margin,
            'sell_margin': sell_margin
        },
        'open_holdings':[],
        'closed_holdings':[]
    })

    # Create start balance w/ all API-enabled exchanges
    for conf in ex_confs():
        g.db['sim_balances'].insert_one({
            'bot_id':r.inserted_id,
            'ex':conf['NAME'],
            'btc':0.0000000,
            'eth':0.0000000,
            'cad':start_cad/len(ex_confs())
        })

    log.info('Created %s bot w/ $%s balance', name, start_cad)

#-------------------------------------------------------------------------------
class SimBot():
    """TODO: determine volatility, adjust buy/sell margins dynamically.
    High volatility == bigger margins, low volatility == lower margins
    """
    _id = None
    name = None
    start_balance = None
    rules = None

    #--------------------------------------------------------------------------
    def update(self):
        self.eval_buys()
        self.eval_sells()
        self.eval_arb()

    #--------------------------------------------------------------------------
    def calc_fee(self, ex, pair, price, vol):
        return ex_confs(name=ex)['TRADE_FEE'][pair] * (vol*price)

    #--------------------------------------------------------------------------
    def buy_market_order(self, ex, pair, ask_price, ask_vol, vol_cap=True):
        max_vol = PAIRS[pair]['MAX_VOL'] if vol_cap else ask_vol
        vol = min(max_vol, ask_vol)
        cost = round(ask_price * vol * -1, 2)
        simex.exec_trade(self._id, ex, pair, 'buy', ask_price, vol, cost)

        log.info('BUY order, ex=%s, pair=%s, %s=%s, %s=%s @ %s',
            ex, pair, pair[0], round(vol,2), pair[1], round(cost,2), ask_price)

    #--------------------------------------------------------------------------
    def sell_market_order(self, buy_trade, bid, bid_vol):
        """Sell at bid price.
        WRITEME: handle eating through > 1 orders
        """
        sold = list(g.db['sim_actions'].aggregate([
            {'$match':{'holding_id':buy_trade['holding_id'],'action':'sell'}},
            {'$group':{'_id':'', 'volume':{'$sum':'$volume'}}}
        ]))
        if len(sold) > 0:
            remaining = buy_trade['volume'] - sold[0]['volume']
        else:
            remaining = buy_trade['volume']
        sell_vol = min(remaining, bid_vol)
        amount = round(bid*sell_vol,2)

        simex.exec_trade(
            self._id, buy_trade['ex'], buy_trade['pair'], 'sell', bid,
            sell_vol, amount, hold_id=buy_trade['holding_id'])

        log.info('SELL order, ex=%s, %s=%s, %s=%s @ %s',
            buy_trade['ex'], buy_trade['pair'][0], round(sell_vol,2),
            buy_trade['pair'][1], round(amount,2), bid)
        return buy_trade

    #--------------------------------------------------------------------------
    def eval_sells(self):
        """Evaluate each open holding, sell on margin criteria
        """
        bot = g.db['sim_bots'].find_one({'_id':self._id})

        for hold_id in bot['open_holdings']:
            buy_trade = g.db['sim_actions'].find_one({'holding_id':hold_id,'action':'buy'})
            buy_trade['pair'] = tuple(buy_trade['pair'])
            bid = simbooks.get_bid(buy_trade['ex'], buy_trade['pair'])
            margin = round(bid[0] - buy_trade['price'], 2)

            if margin >= self.rules['sell_margin']:
                if bid[1] > 0:
                    self.sell_market_order(buy_trade, bid[0], bid[1])
                    smart_emit('updateBot', None)

    #--------------------------------------------------------------------------
    def eval_buys(self):
        """TODO: if market average has moved and no buys for > 1 hour,
        make small buy to reset last buy price
        """
        for conf in ex_confs():
            for pair in conf['PAIRS']:
                BUY=False

                prev = g.db['sim_actions'].find(
                    {'bot_id':self._id, 'ex':conf['NAME'], 'pair':pair, 'action':'buy'}).sort('date',-1).limit(1)
                if prev.count() == 0:
                    log.debug('no holdings for pair=%s. buying', pair)
                    BUY = True

                #else:
                # Buy Indicator A: price dropped
                #recent_trade = holdings[-1]['trades'][0]
                #buy_margin = round(ask['price'] - recent_trade['price'],2)
                #if buy_margin <= self.rules['buy_margin']:
                #    BUY = True

                # Buy Indicator B: low ask inertia
                book_ind = indicators.from_orders(conf['NAME'], pair)

                if book_ind:
                    if book_ind['ask_inertia'] > 0 and book_ind['ask_inertia'] < 15:
                        log.debug('ask_inertia=%s, book=%s, ex=%s. buying',
                        book_ind['ask_inertia'], pair, conf['NAME'])
                        BUY = True

                if BUY:
                    ask = simbooks.get_ask(conf['NAME'], pair)
                    if ask[1] > 0:
                        holding = self.buy_market_order(conf['NAME'], pair, ask[0], ask[1])
                        smart_emit('updateBot', None)

    #--------------------------------------------------------------------------
    def eval_arb(self):
        """Make cross-exchange trade if bid/ask ratio > 1.
        """
        return
        r = g.db['sim_books'].aggregate([
            {'$group':{'_id':'$pair', 'min_ask':{'$min':'$ask'}, 'max_bid':{'$max':'$bid'}}}])

        for book in list(r):
            if book['max_bid']/book['min_ask'] <= 1:
                continue

            buy_simbook = g.db['sim_books'].find_one({'ask':book['min_ask']})
            sell_simbook = g.db['sim_books'].find_one({'bid':book['max_bid']})
            pair = buy_simbook['pair']
            # Match order volume for cross-exchange trade
            vol = min(
                simbooks.get_ask(buy_simbook['ex'], pair)[1],
                simbooks.get_bid(sell_simbook['ex'], pair)[1]
            )
            if vol == 0:
                continue
            buy_p = buy_simbook['asks'][0]['price']
            sell_p = sell_simbook['bids'][0]['price']
            # Calculate net earning
            buy_f = self.calc_fee(buy_simbook['ex'], pair, buy_p, vol)
            sell_f = self.calc_fee(sell_simbook['ex'], pair, sell_p, vol)
            pdiff = round(book['max_bid'] - book['min_ask'],2)
            earn = round(pdiff*vol,2)
            fees = round(buy_f+sell_f,2)
            net_earn = round(earn-fees,2)

            if net_earn <= 50:
                continue

            log.debug('%s=>%s pdiff=%s, v=%s, earn=%s, fees=%s, net_earn=%s',
                buy_simbook['ex'], sell_simbook['ex'], pdiff, vol, earn, fees, net_earn)

            if net_earn >= 100:
                msg = '%s earnings arbitrage window! %s=>%s' %(
                    net_earn, buy_simbook['ex'], sell_simbook['ex'])
                log.warning(msg)
                compose(msg, current_app.config['SMS_ALERT_NUMBER'])

            ### WRITE ME ###
            # Balance checks:
            #   ex-A: CAD >= buy_p*vol
            #   ex-B: BTC >= vol

            holding = self.buy_market_order(
                buy_simbook['ex'],
                pair,
                buy_p,
                vol,
                vol_cap=False)

            # Transfer holding
            holding['exchange'] = sell_simbook['ex']

            self.sell_market_order(
                holding,
                sell_p,
                vol)

            ### WRITE ME ###
            # Balance accounts:
            #   ex-A: transfer BTC=>ex-B
            #   ex-B: transfer CAD=>ex-A

            log.info('TRADE complete, net_earn=%s', net_earn)
            smart_emit('updateBot',None)

    #--------------------------------------------------------------------------
    def holdings(self):
        from pprint import pformat
        bot = g.db['sim_bots'].find_one({'_id':self._id})
        results = []

        for hold_id in bot['open_holdings'] + bot['closed_holdings']:
            b = g.db['sim_actions'].find_one({'holding_id':hold_id})
            s = list(g.db['sim_actions'].aggregate([
                {'$match':{'holding_id':hold_id, 'action':'sell'}},
                {'$group':{
                    '_id':'',
                    'price': {'$avg':'$price'},
                    'fees': {'$sum':'$fee'},
                    'volume': {'$sum':'$volume'},
                    'revenue':{'$sum':'$amount'},
                    'last_date':{'$max':'$date'}
                }}
            ]))

            results.append({
                'ex':b['ex'],
                'pair':b['pair'],
                'open_date':b['date'],
                'volume':b['volume'],
                'buy_price':b['price'],
                'cost':b['amount'],
                'status':b['status'],
                'balance':b['volume'] - (s[0]['volume'] if len(s)>0 else 0),
                'sell_price': s[0]['price'] if len(s)>0 else None,
                'revenue':s[0]['revenue'] if len(s)>0 else None,
                'fees': b['fee'] + (s[0]['fees'] if len(s)>0 else 0),
                'close_date': s[0]['last_date'] if len(s)>0 and b['status']=='closed' else None
            })
        return results

    #--------------------------------------------------------------------------
    def balance(self, ex=None, status=None):
        """Returns dict: {'cad':float, 'btc':float}
        """
        query = {'bot_id':self._id}
        if ex:
            query['ex'] = ex
        #if status:
        #    query['status'] = status

        balance = g.db['sim_balances'].aggregate([
            {'$match':query},
            {'$group':{
                '_id':'',
                'cad':{'$sum':'$cad'},
                'btc':{'$sum':'$btc'},
                'eth':{'$sum':'$eth'}
            }}
        ])
        balance = list(balance)
        return balance[0]

    #--------------------------------------------------------------------------
    def acct_balance(self, exch=None):
        return list(g.db['accounts'].find({'bot_id':self._id}))

    #--------------------------------------------------------------------------
    def total_invested(self, exch=None, status=None):
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        cad_total = 0
        holdings = g.db['holdings'].find(query)
        for h in holdings:
            cad_total += h['trades'][0]['volume'][1]
        return cad_total

    #--------------------------------------------------------------------------
    def n_trades(self, exch=None, status=None):
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        n = 0
        holdings = g.db['holdings'].find(query)
        for h in holdings:
            n += len(h['trades'])
        return n

    #--------------------------------------------------------------------------
    def stats(self, exch=None):
        from app.main import tickers
        return None
        n_open = len(self.holdings(status='open'))
        op_bal = self.balance(status='open')
        op_btc_val = op_bal['btc'] * tickers.summary('QuadrigaCX', ('btc','cad'))
        op_eth_val = op_bal['eth'] * tickers.summary('QuadrigaCX', ('eth','cad'))

        n_closed = len(self.holdings(status='closed'))
        cl_bal = self.balance(status='closed')

        earn = cl_bal['cad'] #- cl_bal['fees']
        cad_invested = self.total_invested()
        btc_gain = op_bal['cad']

        return {
            'accounts': self.acct_balance(),
            'n_trades': self.n_trades(),
            'n_hold_open': n_open,
            'n_hold_closed': n_closed,
            'cad_traded': cad_invested*-1,
            'btc': op_bal['btc'],
            'eth': op_bal['eth'],
            'btc_value': op_btc_val,
            'eth_value': op_eth_val,
            'earnings': earn
        }

    #--------------------------------------------------------------------------
    def __init__(self, name):
        """Load bot properties from Mongo
        """
        bot = g.db['sim_bots'].find_one({'name':name})
        self._id = bot['_id']
        self.rules = bot['rules']
        self.start_balance = bot['start_balance']
        self.name = name
