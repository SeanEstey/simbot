# exchange.py
import logging
from datetime import datetime
from flask import g
from bson import ObjectId
from app.main import exch_conf
from . import simbooks
log = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
def exec_trade(bot_id, ex, book, side, price, vol, cost, hold_id=None):
    """Create new bot trade. Create new holding if BUY, update/close holding if SELL.
    :book: <str> of asset pair.
    :vol, cost: <float> volume traded of left/right-side book assets. vectored.
    :hold_id: ObjectID of holding doc if selling.

    For BUY trade of 'btc_cad' book, vol==btc vol, cost==cad cost.
    """
    # Update sim_books and sim_balances
    fee_pct = exch_conf(ex)['TRADE_FEE'][book]
    fee = fee_pct * abs(cost)
    g.db['sim_balances'].update_one(
        {'bot_id':self._id, 'ex':ex},
        {'$inc':{
            book[0:3] : vol,
            book[4:7] : (cost-fee)
        }}
    )
    simbooks.update(ex, book, side, bot_id, vol)

    # New holding
    if side == 'buy':
        g.db['sim_bots'].update_one(
            {'bot_id':bot_id},
            {'$push':{'open_holdings':trade['holding_id']}}
        )
        status = 'open'
    # Update holding. Check if closed
    elif side == 'sell':
        bought = g.db['sim_actions'].find_one(
            {'holding_id':holding_id,'action':'buy'}
        )
        sold = list(g.db['sim_actions'].aggregate([
            {'$match':{'holding_id':holding_id,'action':'sell'}},
            {'$group':{'_id':'', 'volume':{'$sum':'$volume'}}}
        ]))[0]
        if bought['volume']-sold['volume'] == 0:
            status = 'closed'
            bot = g.db['sim_bots'].find_one({'_id':bot_id})
            # Move hold_id from open_holdings to closed_holdings
            g.db['sim_bots'].update_one(
                {'_id':bot_id},
                {'$set':{
                    'open_holdings': [n for n in bot['open_holdings'] if n!=hold_id]
                }},
                {'$push':{'open_holdings':hold_id}}
            )
        else:
            status = 'open'

    g.db['sim_actions'].insert_one({
        'date':datetime.utcnow(),
        'action':side,
        'bot_id':bot_id,
        'ex': ex,
        'book': book,
        'price': price,
        'volume': vol,
        'cost':cost,
        'fee': fee,
        'holding_id': ObjectId() if side=='buy' else hold_id,
        'status': status
    })

def get(name=None):
    pass

def get_list(pair=None):
    pass

def _merge_order_books():
    pass

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

def sell_market_order(bot_id, name, pair, bid, volume):
    """Consume bid orders until given order volume is sold.
    """
    pass
