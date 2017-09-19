# app.main.simbot
import json
from bson import ObjectId
import requests
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

exchanges = ['ezBTC', 'Coinsquare', 'QuadrigaCX', 'Kraken']

#-------------------------------------------------------------------------------
def process_trade(trade_id):
    """update bots on new trade
    """

    print('trade_id=%s'%trade_id)
    trade = g.db['trades'].find_one({'_id':ObjectId(trade_id)})
    bot = g.db['bots'].find_one({})

    last = g.db['trades'].find(
        {'bot_id':bot['_id'], 'exchange':trade['exchange']}).sort('date',-1).limit(1)

    # First trade on exchange?
    if last.count() < 1:
        log.debug('Making first %s trade.', trade['exchange'])

        balance = get_balance(str(bot['_id']), trade['exchange'])

        if balance['cad'] >= trade['value']:
            make_trade(str(bot['_id']), 'BUY', trade_id)
    # Compare with previous trade
    else:
        last_trade_id = str(list(last)[0]['_id'])
        eval_local(str(bot['_id']), trade_id, last_trade_id)
        eval_arbitrage(str(bot['_id']), trade_id)

#-------------------------------------------------------------------------------
def eval_local(bot_id, trade_id, last_trade_id):
    """Look at most recent trade. These trades have already occurred
    so simulation wouldn't be useful buying backward in time
    """

    bot = g.db['bots'].find_one({'_id':ObjectId(bot_id)})
    rules = bot['rules']
    trade = g.db['trades'].find_one({'_id':ObjectId(trade_id)})
    last = g.db['trades'].find_one({'_id':ObjectId(last_trade_id)})

    p_change = trade['price'] - last['price']

    if p_change > rules['sell_margin']:
        log.debug('diff=%s, exch=%s, order=SELL', p_change, trade['exchange'])
        make_trade(bot_id, 'SELL', trade_id)
    elif p_change < rules['buy_margin']:
        log.debug('diff=%s, exch=%s, order=BUY', p_change, trade['exchange'])
        make_trade(bot_id, 'BUY', trade_id)
    else:
        log.debug('diff=%s, exch=%s', p_change, trade['exchange'])

#-------------------------------------------------------------------------------
def eval_arbitrage(bot_id, trade_id):

    trade = g.db['trades'].find_one({'_id':ObjectId(trade_id)})
    latest = []

    # Get latest trades on each exchange
    for exchange in exchanges:
        last= g.db['trades'].find({'exchange':exchange}).sort('$natural',-1).limit(1)
        if last.count() > 0:
            last = list(last)[0]
            latest.append({
                'exchange':last['exchange'],
                'price': last['price'],
                'diff':round(trade['price']-last['price'],2)
            })

    print(latest)

#-------------------------------------------------------------------------------
def make_trade(bot_id, order_type, trade_id):

    trade = g.db['trades'].find_one({'_id':ObjectId(trade_id)})
    bot = g.db['bots'].find_one({'_id':ObjectId(bot_id)})
    balance = get_balance(bot_id, trade['exchange'])

    if order_type == 'BUY':
        buy_fee = 1.005
        if balance['cad'] < trade['value']*buy_fee:
            log.debug('cad balance too low')
            return
        balance['btc'] += trade['volume']
        balance['cad'] -= trade['value']*buy_fee
        balance['last'] = trade['price']
    elif order_type == 'SELL':
        if trade['volume'] > balance['btc']:
            log.debug('btc balance too low')
            return
        sell_fee = 0.995
        balance['btc'] -= trade['volume']
        balance['cad'] += trade['value']*sell_fee
        balance['last'] = trade['price']

    set_balance(bot_id, trade['exchange'], balance)

    # Mark trade as owned by bot
    g.db['trades'].update_one({'_id':trade['_id']},{'$set':{'bot_id':bot['_id']}})

    trade_fee = round(trade['value']*0.005,2)

    log.info('%s order on %s: BTC=%s for CAD=$%s @ $%s CAD (fee=%s)',
        order_type, trade['exchange'], trade['volume'], trade['value'], trade['price'], trade_fee)

#-------------------------------------------------------------------------------
def create(name, cad):

    cad_each = round(cad/len(exchanges),2)

    balances = []
    for exchange in exchanges:
        balances.append({'exchange':exchange, 'cad':cad_each, 'btc':0.00})

    r = g.db['bots'].insert_one({
        'name':name,
        'start_balance': {
            'cad': cad,
            'btc':0.00
        },
        'balances': balances,
        'trades':[],
        'rules': {
            'buy_margin': -30,
            'sell_margin': 30
        }
    })

    log.info('Created %s bot w/ $%s balance', name, cad)

#-------------------------------------------------------------------------------
def get_balance(bot_id, exchange):

    bot = g.db['bots'].find_one({'_id':ObjectId(bot_id)})

    # Get balance on this exchange
    for i in range(len(bot['balances'])):
        if bot['balances'][i]['exchange'] == exchange:
            return bot['balances'][i]

    return False

#-------------------------------------------------------------------------------
def set_balance(bot_id, exchange, balance):

    bot = g.db['bots'].find_one({'_id':ObjectId(bot_id)})

    for i in range(len(bot['balances'])):
        if bot['balances'][i]['exchange'] == exchange:
            bot['balances'][i] = balance

            g.db['bots'].update_one(
                {'_id':ObjectId(bot_id)},
                {'$set':{'balances':bot['balances']}})

#-------------------------------------------------------------------------------
def summary(name=None):

    bot = g.db['bots'].find_one()
    balances = bot['balances']
    total_cad = 0
    total_btc = 0
    total_btc_value = 0
    earnings = []
    initial_exch_cad = bot['start_balance']['cad']/3

    for exchange in exchanges:
        balance = get_balance(str(bot['_id']), exchange)
        latest = g.db['trades'].find({'exchange':exchange}).sort('$natural',-1).limit(1)
        if latest.count() == 0:
            latest = {'price':0}
        else:
            latest = list(latest)[0]

        earnings.append({
            exchange: round((balance['btc']*latest['price'] + balance['cad']) -
            initial_exch_cad,2)
        })
        total_cad += balance['cad']
        total_btc += balance['btc']
        total_btc_value += (balance['btc'] * latest['price'])

    total_cad = round(total_cad, 2)
    total_btc = round(total_btc, 5)
    total_value = round(total_btc_value + total_cad, 2)
    total_earnings = round(total_value - bot['start_balance']['cad'],2)

    n_trades = g.db['trades'].find({'bot_id':bot['_id']}).count()

    log.info('%s Earnings=%s, CAD=$%s, BTC=%s, nTrades=%s',
        bot['name'].title(), total_earnings, total_cad, total_btc, n_trades)

    print('earnings: %s' % earnings)
