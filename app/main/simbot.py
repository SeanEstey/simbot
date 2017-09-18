# app.main.simbot
import json
from bson import ObjectId
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

    print(r.inserted_id)

    trades = list(g.db['trades'].find({}).sort('date',-1).limit(10))
    for trade in trades:
        if trade['value'] < dollars:
            make_trade(ObjectId(r.inserted_id), 'BUY', trade['transaction_id'])
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

    bots = [g.db['bots'].find_one({'name':name})] if name else list(g.db['bots'].find())

    for bot in bots:
        last_trade = list(g.db['trades'].find({}).limit(1).sort('date',-1))[0]
        btc_value = bot['balance']['coins'] * last_trade['price']
        total_value = round(bot['balance']['dollars'] + btc_value, 2)
        earnings = round(total_value - bot['start_balance']['dollars'], 2)

        log.info('%s Net=$%s, Earnings=$%s, CAD=$%s, BTC=%s, nTrades=%s',
            bot['name'].title(), total_value, earnings, round(bot['balance']['dollars'],2),
            round(bot['balance']['coins'],5), len(bot['trades']))

#-------------------------------------------------------------------------------
def make_trade(bot_id, order_type, tx_id):

    trade = g.db['trades'].find_one({'transaction_id':tx_id})
    bot = g.db['bots'].find_one({'_id':bot_id})

    # TODO: check for necessary balance

    if order_type == 'BUY':
        bot['balance']['coins'] += trade['volume']
        bot['balance']['dollars'] -= trade['value']
    else:
        bot['balance']['coins'] -= trade['volume']
        bot['balance']['dollars'] += trade['value']

    g.db['bots'].update_one(
        {'_id':bot_id},
        {'$set':{'balance':bot['balance']}, '$push':{'trades':trade}})

    # Mark trade as owned by bot
    g.db['trades'].update_one({'_id':trade['_id']},{'$set':{'bot':bot['name']}})

    log.info('%s order, %s BTC, $%s CAD, price=$%s CAD',
        order_type, trade['volume'], trade['value'], trade['price'])

#-------------------------------------------------------------------------------
def update(name=None):
    """Look at most recent trade. These trades have already occurred
    so simulation wouldn't be useful buying backward in time
    """

    bots = [g.db['bots'].find_one({'name':name})] if name else list(g.db['bots'].find())
    ex_trade = list(g.db['trades'].find({}).limit(1).sort('date',-1))[0]

    for bot in bots:

        if len(bot['trades']) == 0:
            bot_trade = ex_trade
            if bot['balance']['dollars'] >= ex_trade['value']:
                make_trade(
                    bot['_id'],
                    'BUY',
                    ex_trade['transaction_id'])
                continue
        else:
            bot_trade = bot['trades'][-1]

            if ex_trade['_id'] == bot_trade['_id']:
                log.debug('tx_id %s already made', str(ex_trade['_id']))
                continue

        rules = bot['rules']

        if ex_trade['price'] > (bot_trade['price'] + rules['sell_margin']):
            if ex_trade['volume'] <= bot['balance']['coins']:
                make_trade(
                    bot['_id'],
                    'SELL',
                    ex_trade['transaction_id'])
        else:
            log.debug('sell price too low')

        if ex_trade['price'] < (bot_trade['price'] + rules['buy_margin']):
            if bot['balance']['dollars'] >= ex_trade['value']:
                make_trade(
                    bot['_id'],
                    'BUY',
                    ex_trade['transaction_id'])
        else:
            log.debug('buy price too high')
