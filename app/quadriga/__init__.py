from __future__ import absolute_import, unicode_literals
from flask import Blueprint
import logging


quadcx = Blueprint(
    'quadcx',
    __name__,
    static_folder='static',
    static_url_path='/static/quadriga',
    template_folder='templates'
)

from .rest_client import RestClient
from .exceptions import *

class QuadrigaClient(object):
    """Python client for QuadrigaCX API v2.

    If only public API calls are required, **api_key**, **api_secret** and
    **client_id** parameters do not need to be set.

    :param api_key: QuadrigaCX API key
    :type api_key: str | unicode
    :param api_secret: QuadrigaCX API secret
    :type api_secret: str | unicode
    :param client_id: QuadrigaCX client ID
    :type client_id: str | unicode
    :param default_book: the default order book
    :type default_book: str | unicode
    """

    # Order books in QuadrigaCX
    order_books = {
        'btc_cad',
        'btc_usd',
        'eth_cad',
        'eth_btc',
        'ltc_cad',
    }

    # Major currencies in QuadrigaCX
    crypto_currencies = {'bitcoin', 'ether', 'litecoin'}

    def __init__(self,
                 api_key=None,
                 api_secret=None,
                 client_id=None,
                 default_book='eth_cad'):
        """Initialize the client.

        :param api_key: QuadrigaCX API key
        :type api_key: str | unicode
        :param api_secret: QuadrigaCX API secret
        :type api_secret: str | unicode
        :param client_id: QuadrigaCX client ID
        :type client_id: str | unicode
        :param default_book: the default order book
        :type default_book: str | unicode
        """
        self._logger = logging.getLogger('quadriga')
        self._rest_client = RestClient(
            api_key=api_key,
            api_secret=api_secret,
            client_id=client_id
        )
        self._client_id = client_id
        self._default_book = self._verify_book(default_book)

    def _log(self, message):
        """Log a debug message.

        :param message: the message to log
        :type message: str | unicode
        """
        self._logger.debug('[client: {}] {}'.format(self._client_id, message))

    def _verify_book(self, book):
        """Verify if the order book is valid and return it (or the default).
        
        :param book: the name of the order book
        :type book: str | unicode
        :returns: the name of the order book to use
        :rtype: str | unicode
        :raises InvalidOrderBookError: on invalid order book name
        """
        if book is None:
            return self._default_book
        if book not in self.order_books:
            raise InvalidOrderBookError(
                'Invalid order book "{}" (choose from {})'
                .format(book, list(self.order_books))
            )
        return book

    def _verify_currency(self, currency):
        """Verify if the currency is valid.
        
        :param currency: the major currency
            (``"bitcoin"``/``"ether"``/``"litecoin"``)
        :type currency: str | unicode
        :raises InvalidCurrencyError: on invalid currency
        """
        if currency not in self.crypto_currencies:
            raise InvalidCurrencyError(
                'Invalid currency "{}" (choose from {})'
                .format(currency, list(self.crypto_currencies))
            )

    def set_default_book(self, book):
        """Update the default order book of the client.

        :param book: the name of the order book
        :type book: str | unicode
        """
        self._default_book = self._verify_book(book)

    def get_summary(self, book=None):
        """Return the latest trading summary.

        :param book: the name of the order book
        :type book: str | unicode
        :returns: the trading summary
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log('get trading summary for ' + book)

        return self._rest_client.get(
            endpoint='/ticker',
            params={'book': book}
        )

    def get_public_orders(self, group=True, book=None):
        """Return all public open orders.

        :param group: group orders with the same price
        :type group: bool
        :param book: the name of the order book
        :type book: str | unicode
        :returns: all public open orders
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log('get public orders for ' + book)

        return self._rest_client.get(
            endpoint='/order_book',
            params={'book': book, 'group': 1 if group else 0}
        )

    def get_public_trades(self, time='hour', book=None):
        """Return recently completed public trades.

        :param time: the time frame (``"minute"`` or ``"hour"``)
        :type time: str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: a list of recent trades
        :rtype: [dict]
        """
        book = self._verify_book(book)
        self._log('get recent public trades for ' + book)

        return self._rest_client.get(
            endpoint='/transactions',
            params={'book': book, 'time': time}
        )

    def get_orders(self, book=None):
        """Return a list of user's open orders.

        :param book: the name of the order book
        :type book: str | unicode
        :returns: a list of user's open orders
        :rtype: [dict]
        """
        book = self._verify_book(book)
        self._log("get user's open orders for " + book)

        return self._rest_client.post(
            endpoint='/open_orders',
            payload={'book': book}
        )

    def get_trades(self, limit=100, offset=0, sort='desc', book=None):
        """Return a list of user's completed trades.

        :param limit: the maximum number of trades to return (0 == all)
        :type limit: int
        :param offset: the number of trades to skip
        :type offset: int
        :param sort: sort by date and time (``"desc"`` or ``"asc"``)
        :type sort: str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: a list of user's completed trades
        :rtype: [dict]
        """
        book = self._verify_book(book)
        self._log("get user's completed trades for " + book)

        return self._rest_client.post(
            endpoint='/user_transactions',
            payload={
                'book': book,
                'limit': limit,
                'offset': offset,
                'sort': sort
            }
        )

    def get_balance(self):
        """Return the user's account balance.

        :returns: the user's account balance
        :rtype: dict
        """
        self._log("get user's account balance")
        return self._rest_client.post(endpoint='/balance')

    def buy_market_order(self, amount, book=None):
        """Buy market order.

        :param amount: the amount of major currency to buy at market price
        :type amount: int | float | str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: the total amount of major currency purchased and a set of
            amount/price pairs, one for each order matched in the trade
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log("buy {} at market price for {}".format(amount, book))

        return self._rest_client.post(
            endpoint='/buy',
            payload={'book': book, 'amount': amount}
        )

    def buy_limit_order(self, amount, price, book=None):
        """Buy limit order.

        :param amount: the amount of major currency to buy at limit price
        :type amount: int | float | str | unicode
        :param price: the limit price to buy at
        :type price: int | float | str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: the details of the order placed
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log("buy {} at price of {} for {}".format(amount, price, book))

        return self._rest_client.post(
            endpoint='/buy',
            payload={'book': book, 'amount': amount, 'price': price}
        )

    def sell_market_order(self, amount, book=None):
        """Sell market order.
        
        :param amount: the amount of major currency to sell at market price
        :type amount: int | float | str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: te total amount of minor currency acquired in sale and a set
            of amount/price pairs, one for each matched in the trade
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log("sell {} at market price for {}".format(amount, book))

        return self._rest_client.post(
            endpoint='/sell',
            payload={'book': book, 'amount': amount}
        )

    def sell_limit_order(self, amount, price, book=None):
        """Sell a limit order.

        :param amount: the amount of the major currency to sell at limit price
        :type amount: int | float | str | unicode
        :param price: the limit price to sell at
        :type price: int | float | str | unicode
        :param book: the name of the order book
        :type book: str | unicode
        :returns: the details of the order placed
        :rtype: dict
        """
        book = self._verify_book(book)
        self._log("sell {} at price of {} for {}".format(amount, price, book))

        return self._rest_client.post(
            endpoint='/sell',
            payload={'book': book, 'amount': amount, 'price': price}
        )

    def lookup_order(self, order_id):
        """Look up an order by its ID

        :param order_id: the ID of the order (64 hexadecmial characters)
        :type order_id: str | unicode
        :returns: ``True`` if order has been found and cancelled
        :rtype: bool
        """
        self._log('look up order {}'.format(order_id))

        return self._rest_client.post(
            endpoint='/lookup_order',
            payload={'id': order_id}
        )

    def cancel_order(self, order_id):
        """Cancel an open order by its ID.

        :param order_id: the ID of the order (64 hexadecmial characters)
        :type order_id: str | unicode
        :returns: ``True`` if order has been found and cancelled
        :rtype: bool
        """
        self._log('cancel order {}'.format(order_id))

        return self._rest_client.post(
            endpoint='/cancel_order',
            payload={'id': order_id}
        )

    def get_deposit_address(self, currency):
        """Return the deposit address for funding on QuadrigaCX.

        :param currency: the major currency
            (``"bitcoin"``/``"ether"``/``"litecoin"``)
        :type currency: str | unicode
        :returns: the user's deposit address on 
        :rtype: str | unicode
        :raises InvalidCurrencyError: on unknown currency
        """
        self._verify_currency(currency)
        self._log('get deposit address for {}'.format(currency))

        return self._rest_client.post(
            endpoint='/{}_deposit_address'.format(currency)
        )

    def withdraw(self, currency, amount, address):
        """Withdraw an amount of currency from QuadrigaCX to user's address.

        :param currency: the major currency
            (``"bitcoin"``/``"ether"``/``"litecoin"``)
        :type currency: str | unicode
        :param amount: the amount to withdraw
        :type amount: int | float | str | unicode
        :param address: the address to send the amount to
        :type address: str | unicode
        :raises InvalidCurrencyError: on unknown currency
        """
        self._verify_currency(currency)
        self._log('withdraw {} {}s to {}'.format(amount, currency, address))

        payload = {'address': address, 'amount': amount}

        return self._rest_client.post(
            endpoint='/{}_withdrawal'.format(currency),
            payload=payload
        )
