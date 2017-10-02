## Overview

Bitcoin/Ethereum trading bot supporting live and simulated trading w/ full client UI support.

Trading logic follows ping-pong (buy low/sell high) and cross-exchange arbitrage. Earning statistics are tracked for each price/volume holding. Settings can be adjusted in config.py.

### Simulation Mode

Real-time trading simulation using live order book data.
Supported: QuadrigaCX [BTC/CAD, ETH/CAD], Coinsquare [BTC/CAD]

### Live Mode

Supported exchanges: QuadrigaCX [BTC/CAD, ETH/CAD]

SMS alerts are sent for arbitrage opportunities on unsupported exchanges.
Monitored exchanges: Coinsquare [BTC/CAD]

## Setup

1. Clone repository
```
git clone https://github.com/SeanEstey/simbot
cd simbot
```
2. Install Ubuntu and python packages in requirements/
3. Run setup.py
4. Create MongoDB credentials file /simbot/db_auth.py:
```
user=username
password=password
```

## Running

1. Start RabbitMQ daemon:
`$ rabbitmqctl start_app`
2. Run:
`python3 run.py <args>`
`-c, --celery`# Start w/ celery worker
`-b, --beat`  # Start w/ celerybeat scheduler
`-d, --debug` # Debug mode

## Shutting Down

If running in foreground, kill with CTRL+C. This will kill Celery workers.
If running in background, get pid:
`$ps aux | grep -m 1 'python main.py' | awk '{print $2}'`
Now kill it using that PID:
`$kill -9 <PID>`
(May need to run twice)
