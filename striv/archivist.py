import logging
import os
import re
import sys
import time
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger('archive-worker')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(
    '%(asctime)s  [%(levelname)s] %(message)s')
)
logger.addHandler(handler)

parser = ArgumentParser(description='Run archive trigger')
parser.add_argument(
    '--max-age',
    type=int,
    default=os.environ.get(
        'STRIV_ARCHIVE_MAX_AGE',
        86400000
    ),
    help='Oldest run to consider on startup in milliseconds'
)
parser.add_argument(
    '--worker-base-url',
    default=os.environ.get(
        'STRIV_WORKER_BASE_URL',
        'http://localhost:8081'
    ),
    help='Base url where striv API is located',
)
parser.add_argument(
    '--archive-interval',
    type=int,
    default=os.environ.get(
        'STRIV_ARCHIVE_INTERVAL',
        60000
    ),
    help='Trigger run log archiving every interval in milliseconds',
)
parser.add_argument(
    '--log-level',
    default=os.environ.get(
        'STRIV_LOG_LEVEL',
        'WARNING'
    ),
    help='One of DEBUG, INFO, WARNING or ERROR'
)


def start_from_max_age(max_age):
    start = datetime.now(timezone.utc) - timedelta(milliseconds=max_age)
    return start.strftime('%Y-%m-%dT%H:%M:%S%z')


def runs_since(base, start):
    '''Generator over all runs since start time.'''
    path = f'/runs?lower={start}'
    while True:
        response = requests.get(base + path)
        if response.status_code != requests.codes['ok']:
            raise RuntimeError(
                f'Failed retrieving runs [start={start}, status={response.status_code}, body={response.text}]')
        for run_id, run in response.json().items():
            logger.debug(
                'Received run [id=%s, status=%s]', run_id, run['status'])
            yield (run_id, run)
        if response.headers.get('Link'):
            path = re.match('<([^>]+)>', response.headers['Link'])[1]
        else:
            break


class UniqueFinishedRuns:
    def __init__(self):
        self.seen_runs = {}

    def process(self, runs):
        '''Generator yielding previously unknown finished runs.'''
        for run_id, run in runs:
            if run['status'] in ['successful', 'failed']:
                if run_id not in self.seen_runs:
                    self.seen_runs[run_id] = run['created_at']
                    yield (run_id, run)

    def prune(self, earliest):
        to_prune = [
            run_id for run_id, created_at in self.seen_runs.items()
            if created_at < earliest
        ]
        for run_id in to_prune:
            del self.seen_runs[run_id]


class OldestUnfinishedRun:
    def __init__(self):
        self.oldest = None

    def process(self, runs):
        '''The oldest observed run that is not done.'''
        for run_id, run in runs:
            if self.oldest is None:
                self.oldest = run['created_at']
            elif run['status'] not in ['successful', 'failed']:
                self.oldest = run['created_at']
            yield (run_id, run)

    def next_start(self):
        return self.oldest


def run_once(start, unique_filter, remember_oldest, base_url):
    runs = unique_filter.process(
        remember_oldest.process(
            runs_since(base_url, start)
        )
    )
    for run_id, run in runs:
        path = f'/run/{run_id}/logs'
        response = requests.get(base_url + path)
        if response.status_code == requests.codes['ok']:
            logger.info(
                'Triggering log archiving [run=%s. created=%s]',
                run_id,
                run['created_at']
            )
        else:
            logger.warning(
                'Log archiving failed [run=%s. created=%s, status=%d, body=%s]',
                run_id,
                run['created_at'],
                response.status_code,
                response.text
            )
    start = remember_oldest.next_start() or start
    unique_filter.prune(start)
    return start


def run(args):
    start = start_from_max_age(args.max_age)
    unique_filter = UniqueFinishedRuns()
    remember_oldest = OldestUnfinishedRun()
    logger.warning(
        'Archivist starting [base_url=%s, start=%s, interval=%d]',
        args.worker_base_url,
        start,
        args.archive_interval
    )
    while True:
        start = run_once(start, unique_filter,
                         remember_oldest, args.worker_base_url)
        time.sleep(args.archive_interval / 1000.0)


if __name__ == '__main__':
    args = parser.parse_args()
    logger.setLevel(args.log_level)
    run(args)
