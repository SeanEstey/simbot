from __future__ import absolute_import, unicode_literals

import hashlib
import hmac
import time

import requests

from .exceptions import RequestError


class RestClient(object):
    """Utility HTTP client which handles HMAC SHA256 authentication."""

    endpoint_prefix = 'https://api.quadrigacx.com/v2'

    def __init__(self,
                 api_key=None,
                 api_secret=None,
                 client_id=None):
        """Wrapper for sending requests to QuadrigaCX.

        Authentication using HMAC SHA256 is carried out here.

        :param api_key: the API key from QuadrigaCX
        :type api_key: str | unicode
        :param api_secret: the API secret from QuadrigaCX
        :type api_secret: str | unicode
        :param client_id: the QuadrigaCX client ID
        :type client_id: str | unicode
        """
        self._api_key = str(api_key)
        self._hmac_key = str(api_secret).encode('utf-8')
        self._client_id = str(client_id)
        self._http_success = {code for code in range(200, 210)}

    def _compute_signature(self, nonce):
        """Compute the signature using HMAC SHA256 for authentication.

        :param nonce: an integer unique to each API call
        :type nonce: int
        :return: the signature computed using HMAC SHA256
        :rtype: str | unicode
        """
        msg = str(nonce) + self._client_id + self._api_key
        return hmac.new(
            key=self._hmac_key,
            msg=msg.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

    def _handle_response(self, response):
        """Handle the response from QuadrigaCX.

        :param response: the response from QuadrigaCX
        :type response: requests.models.Response
        :returns: the JSON response body
        :rtype: dict
        :raises QuadrigaRequestError: HTTP 2XX was not returned
        """
        http_code = response.status_code
        if http_code not in self._http_success:
            raise RequestError(
                response=response,
                message='[HTTP {}] {}'.format(
                    http_code, response.reason
                )
            )
        try:
            body = response.json()
        except ValueError:
            raise RequestError(
                response=response,
                message='[HTTP {}] response body: {}'.format(
                    http_code, response.text
                )
            )
        else:
            if 'error' in body:
                error_code = body['error'].get('code', '?')
                raise RequestError(
                    response=response,
                    message='[HTTP {}][ERR {}] {}'.format(
                        response.status_code,
                        error_code,
                        body['error'].get('message', 'no error message')
                    ),
                    error_code=error_code
                )
            return body

    def get(self, endpoint, params=None):
        """Send an HTTP GET request to QuadrigaCX.

        :param endpoint: the API endpoint/path
        :type endpoint: str | unicode
        :param params: the request parameters
        :type params: dict
        :returns: the JSON response body from QuadrigaCX
        :rtype: dict
        """
        response = requests.get(
            url=self.endpoint_prefix + endpoint,
            params=params
        )
        return self._handle_response(response)

    def post(self, endpoint, payload=None):
        """Send an HTTP POST request to QuadrigaCX.

        :param endpoint: the API endpoint/path
        :type endpoint: str | unicode
        :param payload: the request payload
        :type payload: dict
        :return: the JSON response body from QuadrigaCX
        :rtype: dict
        """
        nonce = int(time.time() * 1000)
        signature = self._compute_signature(nonce)

        if payload is None:
            payload = {}
        payload['key'] = self._api_key
        payload['nonce'] = nonce
        payload['signature'] = signature

        response = requests.post(
            url=self.endpoint_prefix + endpoint,
            json=payload
        )
        return self._handle_response(response)
