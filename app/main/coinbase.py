# app.main.coinbase
import json
import requests
from flask import g
from app.lib.timer import Timer
from logging import getLogger
log = getLogger(__name__)


def websock():
    import gdax, time
    order_book = gdax.OrderBook(product_id='BTC-USD')
    order_book.start()
    time.sleep(10)
    order_book.close()

#-------------------------------------------------------------------------------
def ticker():

    import gdax
    client = gdax.PublicClient()
    # Get the order book at the default level.
    products = client.get_products()
    log.info('products=%s', products)

    book = client.get_product_order_book('BTC-CAD')
    # Get the product ticker for a specific product.
    tick = client.get_product_ticker(product_id='BTC-CAD')

    log.info('book=%s', book)
    log.info('tick=%s', tick)


