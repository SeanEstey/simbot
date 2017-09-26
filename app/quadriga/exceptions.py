from __future__ import absolute_import, unicode_literals


class QuadrigaError(Exception):
    """Base class for all Quadriga exceptions."""


class RequestError(QuadrigaError):
    """Raised when there is an issue with sending requests to QuadrigaCX."""

    def __init__(self, response, message, error_code=None):
        self.url = response.url
        self.body = response.text
        self.headers = response.headers
        self.http_code = response.status_code
        self.error_code = error_code
        self.error_msg = message
        Exception.__init__(self, message)


class InvalidCurrencyError(QuadrigaError):
    """Raised when an invalid currency is specified."""


class InvalidOrderBookError(QuadrigaError):
    """Raised when an invalid order book name is specified."""
