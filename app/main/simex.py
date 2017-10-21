# exchange.py
import logging
from datetime import datetime
from flask import g
from bson import ObjectId
from app.main import ex_confs
from . import simbooks
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
def exec_trade(bot_id, ex, pair, side, price, vol, amount, hold_id=None):
    """Create new bot trade. Create new holding if BUY, update/close holding if SELL.
    :book: <str> of asset pair.
    :vol, cost: <float> volume traded of left/right-side book assets. vectored.
    :hold_id: ObjectID of holding doc if selling.

    For BUY trade of 'btc_cad' book, vol==btc vol, cost==cad cost.
    """
    # Update sim_books and sim_balances
    exconf = ex_confs(name=ex)
    fee_pct = exconf['PAIRS'][pair]['fee']
    fee = fee_pct * abs(amount)
    g.db['sim_balances'].update_one(
        {'bot_id':bot_id, 'ex':ex},
        {'$inc':{
            pair[0] : vol,
            pair[1] : (amount-fee)
        }}
    )
    simbooks.update(ex, pair, 'asks' if side=='buy' else 'bids', bot_id, vol)

    status = 'open'

    # New holding
    if side == 'buy':
        hold_id=ObjectId()
        r=g.db['sim_bots'].update_one(
            {'_id':bot_id},
            {'$push':{'open_holdings':hold_id}}
        )
    # Update holding. Check if closed
    elif side == 'sell':
        bought = g.db['sim_actions'].find_one(
            {'holding_id':hold_id,'action':'buy'}
        )
        sold = list(g.db['sim_actions'].aggregate([
            {'$match':{'holding_id':hold_id,'action':'sell'}},
            {'$group':{'_id':'', 'volume':{'$sum':'$volume'}}}
        ]))
        #log.debug('hold_id=%s, bought=%s, sold=%s', hold_id, bought, sold)
        if len(sold) > 0:
            if bought['volume']-sold[0]['volume'] == 0:
                #log.info('holding is closed!')
                status = 'closed'
                bot = g.db['sim_bots'].find_one({'_id':bot_id})
                # Move hold_id from open_holdings to closed_holdings
                g.db['sim_bots'].update_one(
                    {'_id':bot_id},
                    {
                        '$set':{'open_holdings': [n for n in bot['open_holdings'] if n!=hold_id]},
                        '$push':{'closed_holdings':hold_id}
                    }
                )
                g.db['sim_actions'].update_many({'holding_id':hold_id},{'$set':{'status':'closed'}})

    g.db['sim_actions'].insert_one({
        'date':datetime.utcnow(),
        'action':side,
        'bot_id':bot_id,
        'ex': ex,
        'pair': pair,
        'price': price,
        'volume': abs(vol),
        'amount':abs(amount),
        'fee': fee,
        'holding_id': hold_id,
        'status': status
    })

#-------------------------------------------------------------------------------
def fill_limit_order(bot_id, name, pair, section, volume):
    """Fill limit order volume by given amount.
    """
    ex = g.db['exchanges'].find_one({'name':name, 'book':pair})
    order = ex[section][0]

    if order.get('bot_consumed'):
        order['bot_consumed'] += volume
    else:
        order['bot_consumed'] = volume

    order['bot_id'] = bot_id
    ex[section][0] = order

    g.db['exchanges'].update_one(
        {'_id':ex['_id']},
        {'$set':{
            section: ex[section]
        }}
    )

#-------------------------------------------------------------------------------
def buy_market_order(bot_id, name, pair, ask, volume):
    """Keep consuming ask orders until given order volume is bought.
    """
    vol_filled=0
    next_ask = True

    while vol_filled <= volume and next_ask:
        # Consume orders
        vol_filled+=next_ask['volume']
        next_ask = True # Get next ask
        continue

#-------------------------------------------------------------------------------
def sell_market_order(bot_id, name, pair, bid, volume):
    """Consume bid orders until given order volume is sold.
    """
    pass
