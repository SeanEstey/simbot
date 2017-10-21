"""Class: SimBot
"""
import logging
from flask import g, current_app
from app.main import exch_conf, pair_conf
from app.lib.timer import Timer
from bson import ObjectId as oid
from . import simbooks
from app.main.sms import compose
from app.main.socketio import smart_emit
from app.main import indicators
log = logging.getLogger(__name__)

#---------------------------------------------------------------
def pair_names(pair_str):
    div_idx = pair_str.index('_')
    return [ pair_str[0:div_idx], pair_str[div_idx+1:] ]

#-------------------------------------------------------------------------------
def get_ex(exch=None, pair=None):
    query = {}
    if exch:
        query['name'] = exch
    if pair:
        query['book'] = pair
    return list(g.db['sim_books'].find(query))

#-------------------------------------------------------------------------------
def create(name, start_cad, buy_margin, sell_margin):
    from config import EXCHANGES
    ex_confs = [n for n in EXCHANGES if n['API_ENABLED'] == True]

    r = g.db['sim_bots'].insert_one({
        'name':name,
        'start_balance': start_cad,
        'rules': {
            'buy_margin': buy_margin,
            'sell_margin': sell_margin
        }})

    # Create start balance w/ all API-enabled exchanges
    for conf in ex_confs:
        g.db['sim_balances'].insert_one({
            'bot_id':r.inserted_id,
            'ex':conf['NAME'],
            'btc':0.0000000,
            'eth':0.0000000,
            'cad':start_cad/len(ex_confs)
        })

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
    def add_holding(self, exch, pair, trade):
        """status values: 'pending', 'open', 'closed'
        """
        r = g.db['holdings'].insert_one({
            'bot_id':self._id,
            'exchange':exch,
            'status':'open',
            'fees':trade['fee'],
            'pair': pair,
            'balance': trade['volume'],
            'trades':[trade]
        })
        return g.db['holdings'].find_one({'_id':oid(r.inserted_id)})

    #---------------------------------------------------------------
    def holdings(self, exch=None, pair=None, status=None):
        """status values: 'pending', 'open', 'closed'
        """
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        if pair:
            query['pair'] = pair
        return list(g.db['holdings'].find(query))

    #---------------------------------------------------------------
    def calc_fee(self, exch, pair, price, vol):
        return exch_conf(exch)['TRADE_FEE'][pair] * (vol*price)

    #---------------------------------------------------------------
    def update_balance(self, exch, asset, volume):
        bal = g.db['accounts'].find_one({'bot_id':self._id, 'name':exch})
        g.db['accounts'].update_one({'_id':bal['_id']},{'$set':{asset:bal[asset]+volume}})

    #---------------------------------------------------------------
    def add_trade(self, exch, book, _type, price, pair_vol, holding=None):
        """Add a BUY/SELL trade to given holding, closing it if
        sell balance reaches 0.

        :pair_vol: list w/ float pair (i.e [0.1111,-500.00] for
        buy order of BTC priced in CAD
        """
        fee_pct = exch_conf(exch)['TRADE_FEE'][book]
        fee = fee_pct * abs(pair_vol[1])
        trade = {
            'type' :_type,
            'price': price,
            'volume': pair_vol,
            'fee': fee
        }

        self.update_balance(exch, book[0:3], pair_vol[0])
        self.update_balance(exch, book[4:], pair_vol[1] - fee)

        if holding is None:
            return self.add_holding(exch, book, trade)
        else:
            holding['trades'].append(trade)
            holding['balance'][0] += pair_vol[0]
            holding['balance'][1] += pair_vol[1]
            holding['fees'] += trade['fee']
            if holding['balance'][0] == 0:
                holding['status'] = 'closed'
            g.db['holdings'].update_one({'_id':holding['_id']},{'$set':holding})
            return holding

    #---------------------------------------------------------------
    def buy_market_order(self, ex, book, ask_price, ask_vol, vol_cap=True):
        max_vol = pair_conf(book)['MAX_VOL'] if vol_cap else ask_vol
        vol = min(max_vol, ask_vol)
        cost = round(ask_price * vol * -1, 2)
        simbooks.update(ex, book, 'asks', self._id, vol)
        holding = self.add_trade(ex, book, 'BUY', ask_price, [vol, cost])

        # NEW
        simex.exec_trade(self._id, ex, book, 'buy', ask_price, vol, cost)

        log.info('BUY order, ex=%s, %s=%s, %s=%s @ %s',
            ex, pair_names(book)[0], round(vol,2), pair_names(book)[1],
            round(cost,2), ask_price)
        return holding

    #---------------------------------------------------------------
    def sell_market_order(self, holding, bid, bid_vol):
        """Sell at bid price.
        WRITEME: handle eating through > 1 orders
        """
        balance = holding['balance']
        loss_vol = min(balance[0], bid_vol)
        gain_vol = round(bid*loss_vol,2)
        simbooks.update(holding['exchange'], holding['pair'], 'bids', self._id, loss_vol)
        holding = self.add_trade(
            holding['exchange'],
            holding['pair'],
            'SELL',
            bid,
            [loss_vol*-1, gain_vol],
            holding=holding)

        # NEW
        simex.exec_trade(self._id, holding['exchange']ex, book, 'buy', ask_price, vol, cost)

        log.info('SELL order, exch=%s, %s=%s, %s=%s @ %s',
            holding['exchange'],
            pair_names(holding['pair'])[0], round(loss_vol,2),
            pair_names(holding['pair'])[1], round(gain_vol,2), bid)
        return holding

    #---------------------------------------------------------------
    def sell_limit_order(self, holding, price, vol):
        """Place a limit order on the books. Price below top ask
        for quickest trade
        """
        pass

    #---------------------------------------------------------------
    def update(self):
        self.eval_buy_positions()
        self.eval_sell_positions()
        self.eval_arbitrage()

    #---------------------------------------------------------------
    def eval_sell_positions(self):
        """Evaluate each open holding, sell on margin criteria
        """
        _holdings = self.holdings(status='open')
        for i in range(len(_holdings)):
            holding = _holdings[i]
            ex = get_ex(exch=holding['exchange'], pair=holding['pair'])[0]
            bid = simbooks.get_bid(ex['name'], ex['book'])
            margin = round(bid['price'] - holding['trades'][0]['price'],2)

            if margin >= self.rules['sell_margin']:
                self.sell_market_order(holding, bid['price'], bid['volume'])
                smart_emit('updateBot', None)

    #---------------------------------------------------------------
    def eval_buy_positions(self):
        """TODO: if market average has moved and no buys for > 1 hour,
        make small buy to reset last buy price
        """
        for ex in get_ex():
            BUY = False
            ask = simbooks.get_ask(ex['name'], ex['book'])
            holdings = self.holdings(exch=ex['name'], pair=ex['book'])

            if len(holdings) == 0:
                BUY = True
            else:
                # Buy Indicator A: price dropped
                recent_trade = holdings[-1]['trades'][0]
                buy_margin = round(ask['price'] - recent_trade['price'],2)
                if buy_margin <= self.rules['buy_margin']:
                    BUY = True

                # Buy Indicator B: low ask inertia
                book_ind = indicators.from_orders(ex['name'], ex['book'])

                if book_ind:
                    if book_ind['ask_inertia'] > 0 and book_ind['ask_inertia'] < 15:
                        log.debug('ask_inertia=%s, book=%s, ex=%s. buying',
                        book_ind['ask_inertia'], ex['book'], ex['name'])
                        BUY = True

            if BUY:
                holding = self.buy_market_order(
                    ex['name'],
                    ex['book'],
                    ask['price'],
                    ask['volume'])
                smart_emit('updateBot', None)

    #---------------------------------------------------------------
    def eval_arbitrage(self):
        """Make cross-exchange trade if bid/ask ratio > 1.
        """
        r = g.db['sim_books'].aggregate([
            {'$group':{'_id':'$book', 'min_ask':{'$min':'$ask'}, 'max_bid':{'$max':'$bid'}}}])

        for book in list(r):
            if book['max_bid']/book['min_ask'] <= 1:
                continue

            buy_ex = g.db['sim_books'].find_one({'ask':book['min_ask']})
            sell_ex = g.db['sim_books'].find_one({'bid':book['max_bid']})
            pair = buy_ex['book']
            # Match order volume for cross-exchange trade
            vol = min(
                simbooks.get_ask(buy_ex['name'], pair)['volume'],
                simbooks.get_bid(sell_ex['name'], pair)['volume']
            )
            if vol == 0:
                continue
            buy_p = buy_ex['asks'][0]['price']
            sell_p = sell_ex['bids'][0]['price']
            # Calculate net earning
            buy_f = self.calc_fee(buy_ex['name'], pair, buy_p, vol)
            sell_f = self.calc_fee(sell_ex['name'], pair, sell_p, vol)
            pdiff = round(book['max_bid'] - book['min_ask'],2)
            earn = round(pdiff*vol,2)
            fees = round(buy_f+sell_f,2)
            net_earn = round(earn-fees,2)

            if net_earn <= 50:
                continue

            log.debug('%s=>%s pdiff=%s, v=%s, earn=%s, fees=%s, net_earn=%s',
                buy_ex['name'], sell_ex['name'], pdiff, vol, earn, fees, net_earn)

            if net_earn >= 100:
                msg = '%s earnings arbitrage window! %s=>%s' %(
                    net_earn, buy_ex['name'], sell_ex['name'])
                log.warning(msg)
                compose(msg, current_app.config['SMS_ALERT_NUMBER'])

            ### WRITE ME ###
            # Balance checks:
            #   ex-A: CAD >= buy_p*vol
            #   ex-B: BTC >= vol

            holding = self.buy_market_order(
                buy_ex['name'],
                pair,
                buy_p,
                vol,
                vol_cap=False)

            # Transfer holding
            holding['exchange'] = sell_ex['name']

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

    #---------------------------------------------------------------
    def balance(self, exch=None, status=None):
        """Returns dict: {'cad':float, 'btc':float}
        """
        query = {'bot_id':self._id}
        if exch:
            query['exchange'] = exch
        if status:
            query['status'] = status
        pairs = [
            {'pair':'btc_cad', 'l_pair':'btc'},
            {'pair':'eth_cad', 'l_pair':'eth'}
        ]
        results = []

        for p in pairs:
            query['pair'] = p['pair']

            grp = {
                '_id':'',
                'fees':{'$sum':'$fees'},
                p['l_pair']: {'$sum':{'$arrayElemAt':['$balance',0]}},
                'cad':{'$sum':{'$arrayElemAt':['$balance',1]}}}
                # {'$sum':{'$arrayElemAt':['$arrayElemAt':['$trades',0], 1]}

            r = g.db['holdings'].aggregate([
                {'$match':query},
                {'$group':grp},
                {'$project':{'_id':0, 'fees':1, 'cad':1, p['l_pair']:1}}
            ])
            r = list(r)
            if len(r) > 0:
                results.append(r[0])
            else:
                results.append({})

        bal = {
            'cad': results[0].get('cad',0) + results[1].get('cad',0),
            'eth': results[1].get('eth',0),
            'btc': results[0].get('btc',0),
            'fees': results[0].get('fees',0) + results[1].get('fees',0)
        }
        return bal

    #---------------------------------------------------------------
    def acct_balance(self, exch=None):
        return list(g.db['accounts'].find({'bot_id':self._id}))

    #---------------------------------------------------------------
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

    #---------------------------------------------------------------
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

    #---------------------------------------------------------------
    def stats(self, exch=None):
        n_open = len(self.holdings(status='open'))
        op_bal = self.balance(status='open')
        op_btc_val = op_bal['btc'] * get_ex(pair='btc_cad')[0]['bid']
        op_eth_val = op_bal['eth'] * get_ex(pair='eth_cad')[0]['bid']

        n_closed = len(self.holdings(status='closed'))
        cl_bal = self.balance(status='closed')

        earn = cl_bal['cad'] - cl_bal['fees']
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

    #---------------------------------------------------------------
    def __init__(self, name):
        """Load bot properties from Mongo
        """
        bot = g.db['bots'].find_one({'name':name})
        self._id = bot['_id']
        self.rules = bot['rules']
        self.start_balance = bot['start_balance']
        self.name = name
