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

spinner = itertools.cycle(['-', '/', '|', '\\'])
client = pymongo.MongoClient(
    host='localhost',
    port=27017,
    tz_aware=True,
    connect=True)
db = client['simbot']

def connect(endpoint):
    websocket.enableTrace(True)
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

    while ws.sock.connected:
        update_spinner()

def on_message(ws, message):
    trade = json.loads(message)
    print(trade)
    trade['date'] = parse(trade['date'])
    db['trades'].insert_one(trade)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    connect()

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

def update_spinner():
    sys.stdout.write(next(spinner))
    sys.stdout.flush()
    sys.stdout.write('\b')
    sleep(1)

if __name__ == "__main__":
    endpoint = sys.argv[1]
    connect(endpoint)
