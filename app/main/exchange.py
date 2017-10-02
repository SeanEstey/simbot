# exchange.py

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
