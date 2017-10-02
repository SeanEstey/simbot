# sms.py
from twilio.rest import Client
from flask import g
from logging import getLogger
from app import get_key

log = getLogger(__name__)

#-------------------------------------------------------------------------------
def compose(body, to, callback=None):
    """Send SMS message. Returns delivery status.

    :to: destination phone number in international format
         '+17801234567'
    """
    keys = get_key('twilio')

    try:
        client = Client(keys['api']['sid'], keys['api']['auth_id'])
        msg = client.messages.create(
            body=body, to=to, from_=keys['sms']['number'], status_callback=None)
    except Exception as e:
        log.exception('Error creating twilio client or sending msg')
        raise

    log.debug(body)
    return msg.status
