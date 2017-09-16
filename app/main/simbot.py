# app.main.simbot
import json
import requests
from logging import getLogger
from flask import g
from app.lib.timer import Timer
log = getLogger(__name__)

#-------------------------------------------------------------------------------
def create(name, dollars, currency, coin_name):

    r = g.db['bots'].insert_one({
        'name':name,
        'coin_name':coin_name,
        'currency': currency,
        'start_balance': {
            'dollars': dollars,
            'coins':0.00
        },
        'balance': {
            'dollars':dollars,
            'coins': 0.00
        },
        'trades':[],
        'rules': {
            'buy_margin': -10,
            'sell_margin': 30
        },
        'earnings':0
    })

    trades = list(g.db['trades'].find({}).sort('date',-1).limit(10))

    for trade in trades:
        if trade['value'] < dollars:
            make_trade(r.inserted_id, 'BUY', trade['tx_id'])
            break

    log.info('Created %s bot w/ $%s balance', name, dollars)

#-------------------------------------------------------------------------------
def get(name=None):

    if name:
        return g.db['bots'].find_one({'name':name})
    else:
        return g.db['bots'].find()

#-------------------------------------------------------------------------------
def summary(name=None):

    if name:
        bot = g.db['bots'].find_one({'name':name})
        log.info('%s bot summary: dollars=%s, coins=%s, n_trades=%s',
            name, bot['balance']['dollars'], bot['balance']['coins'], len(bot['trades']))
        return bot
    else:
        bots = list(g.db['bots'].find({'name':name}))
        for bot in bots:
            log.info('%s bot summary: dollars=%s, coins=%s, n_trades=%s',
                name, bot['balance']['dollars'], bot['balance']['coins'], len(bot['trades']))
        return bots

#-------------------------------------------------------------------------------
def make_trade(bot_id, order_type, tx_id):

    trade = g.db['trades'].find_one({'transaction_id':tx_id})
    bot = g.db['bots'].find_one({'_id':bot_id})

    # TODO: check for necessary balance

    if order_type == 'BUY':
        bot['balance']['coins'] += trade['volume']
        bot['balance']['dollars'] -= trade['value']
        action = 'bought'
    else:
        bot['balance']['coins'] -= trade['volume']
        bot['balance']['dollars'] += trade['value']
        action = 'sold'

    bot = g.db['bots'].update_one(
        {'_id':bot_id},
        {'$set':{'balance':bot['balance'], '$push':{'trades':trade}}})

    # Mark trade as owned by bot
    g.db['trades'].update_one({'_id':trade['_id']},{'$set':{'bot':bot['name']}})

    log.info('%s %s %sbtc@$%s for $%s',
        bot['name'], action, trade['volume'], trade['price'], trade['value'])

#-------------------------------------------------------------------------------
def update(name):

    bot = g.db['bots'].find_one({'name':name})
    rules = bot['rues']
    bot_trade = bot['trades'][-1]

    # Look at most recent trade. These trades have already occurred
    # so simulation wouldn't be useful buying backward in time
    ex_trade = g.db['trades'].find_one({}).limit(1).sort('date',-1)

    if ex_trade['price'] > (bot_trade['price'] + rules['sell_margin']):

        #TODO: BALANCE CHECK

        make_trade(
            bot['_id'],
            'SELL',
            ex_trade['transaction_id'])
    elif ex_trade['price'] < (bot_trade['price'] + rules['buy_margin']):

        #TODO: BALANCE CHECK

        make_trade(
            bot['_id'],
            'BUY',
            ex_trade['transaction_id'])

    summary(name)
