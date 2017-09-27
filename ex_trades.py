"""ex_trades.py
Creates websocket connection to exchange endpoint, saves trade data to MongoDB.
Python: 3.5+
Requirements: websocket-client, pymongo
To run:
    $ python3.5 ex_trades.py endpoint
To quit: CTRL+C
Endpoints:
    CBIX index: wss://socket.cbix.ca/index
    CBIX trades: wss://socket.cbix.ca/trades
"""

import os, sys, threading, signal
from datetime import datetime
from dateutil.parser import parse
from time import sleep
import pymongo
import json
import websocket
import itertools
import requests

spinner = itertools.cycle(['-', '/', '|', '\\'])
client = pymongo.MongoClient(
    host='localhost',
    port=27017,
    tz_aware=True,
    connect=True)
db = client['simbot']

def connect(endpoints):
    """Main thread
    """
    websocket.enableTrace(True)

    for endpoint in endpoints:
        ws = websocket.WebSocketApp(endpoint,
            on_message = on_message,
            on_error = on_error,
            on_close = on_close)
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

    sleep(1)
    conn_timeout = 180
    while not ws.sock.connected and conn_timeout:
        sleep(1)
        conn_timeout -= 1

    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to quit')

    # Loops forever after socket is connected.
    while ws.sock.connected:
        update_spinner()
        get_prices()

def on_message(ws, message):
    """Daemon websocket thread.
    """
    data = json.loads(message)
    # Trade
    if 'transaction_id' in data:
        data['currency'] = 'btc'
        data['date'] = parse(data['date'])
        r = db['trades'].insert_one(data)

        print('%s, p=%s, v=%s, t=%s' %(
            data['exchange'], data['price'], data['volume'], data['value']))

def on_error(ws, error):
    """Daemon thread
    """
    print(error)

def on_close(ws):
    """Daemon thread
    """
    print("### closed ###")
    connect()

def signal_handler(signal, frame):
    """Main thread
    """
    print('You pressed Ctrl+C!')
    sys.exit(0)

def get_prices():
    """Main thread
    """
    pass

def update_spinner():
    """Main thread
    """
    msg = 'listening %s' % next(spinner)
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stdout.write('\b'*len(msg))
    sleep(1)

if __name__ == "__main__":
    # Get endpoint subscription list
    #endpoint = sys.argv[1:]
    print('%s endpoints...' % len(sys.argv[1:]))
    connect(sys.argv[1:])
