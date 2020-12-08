import logging
import os
import sys
import time
from argparse import ArgumentParser

import requests

logger = logging.getLogger('refresh-worker')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(
    '%(asctime)s  [%(levelname)s] %(message)s')
)
logger.addHandler(handler)

parser = ArgumentParser(description='Run refresh worker')
parser.add_argument(
    '--worker-base-url',
    default=os.environ.get(
        'STRIV_WORKER_BASE_URL',
        'http://localhost:8081'
    ),
    help='Base url where striv API is located',
)
parser.add_argument(
    '--refresh-interval',
    default=os.environ.get(
        'STRIV_REFRESH_INTERVAL',
        60000
    ),
    help='Run refresh interval in milliseconds',
)
parser.add_argument(
    '--refresh-backoff',
    default=os.environ.get(
        'STRIV_REFRESH_BACKOFF',
        5000
    ),
    help='Backoff interval in case of striv API failure'
)
parser.add_argument(
    '--log-level',
    default=os.environ.get(
        'STRIV_LOG_LEVEL',
        'WARNING'
    ),
    help='One of DEBUG, INFO, WARNING or ERROR'
)


def run(args):
    while True:
        response = requests.post(args.worker_base_url + '/runs/refresh-all')
        if response.status_code == requests.codes['ok']:
            logger.info('Requesting run refresh: %s', response.json())
            time.sleep(args.refresh_interval / 1000.0)
        else:
            logger.warning('Failed to request runs: %s', response.text)
            time.sleep(args.refresh_backoff / 1000.0)


if __name__ == '__main__':
    args = parser.parse_args()
    logger.setLevel(args.log_level)
    run(args)
