# pylint: disable = missing-function-docstring, redefined-outer-name
import pytest
import requests_mock

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import errors, nomad_logstore
from . import nomad_allocs

DRIVER_CONFIG = {
    'nomad_url': 'http://localhost'
}

ALLOC_ENDPOINT = DRIVER_CONFIG['nomad_url'] + '/v1/allocation/alloc-2'
LOGS_ENDPOINT = DRIVER_CONFIG['nomad_url'] + '/v1/client/fs/logs/alloc-2'


@pytest.fixture
def logstore():
    return nomad_logstore


@pytest.fixture
def nomad():
    with requests_mock.Mocker() as mock:
        yield mock


def test_fetch_log_summary_returns_all_log_streams(logstore, nomad):
    nomad.get(ALLOC_ENDPOINT, json=nomad_allocs.running_alloc)
    nomad.get(LOGS_ENDPOINT, text='ze-log')
    assert logstore.fetch_log_summary(DRIVER_CONFIG, 'alloc-2') == {
        'task-1/stderr': 'ze-log',
        'task-1/stdout': 'ze-log',
    }


def test_fetch_log_summary_requests_part_of_log(logstore, nomad):
    nomad.get(ALLOC_ENDPOINT, json=nomad_allocs.running_alloc)
    nomad.get(LOGS_ENDPOINT, text='ze-log')
    logstore.fetch_log_summary(DRIVER_CONFIG, 'alloc-2')
    assert_that(nomad.last_request.qs, has_entry('offset', ['2000']))


def test_fetch_log_summary_raises_not_found_on_unknown_alloc(logstore, nomad):
    nomad.get(ALLOC_ENDPOINT, status_code=404)
    assert_that(
        calling(logstore.fetch_log_summary).with_args(
            DRIVER_CONFIG, 'alloc-2'),
        raises(errors.RunNotFound)
    )


def test_fetch_log_summary_skips_missing_streams(logstore, nomad):
    nomad.get(ALLOC_ENDPOINT, json=nomad_allocs.running_alloc)
    nomad.get(LOGS_ENDPOINT + '?type=stderr', status_code=400, text='boom!')
    nomad.get(LOGS_ENDPOINT + '?type=stdout', text='ze-log')
    assert_that(
        logstore.fetch_log_summary(DRIVER_CONFIG, 'alloc-2'),
        has_entries({
            'task-1/stderr': matches_regexp('boom!'),
            'task-1/stdout': 'ze-log',
        })
    )


def test_fetch_log(logstore, nomad):
    nomad.get(LOGS_ENDPOINT + '?type=stdout', text='ze-log')
    assert logstore.fetch_log(
        DRIVER_CONFIG, 'alloc-2', 'task-1/stdout'
    ) == 'ze-log'


def test_fetch_log_raises_not_found(logstore, nomad):
    nomad.get(LOGS_ENDPOINT + '?type=stdout', status_code=404)
    assert_that(
        calling(logstore.fetch_log).with_args(
            DRIVER_CONFIG, 'alloc-2', 'task-1/stdout'
        ),
        raises(errors.RunNotFound)
    )
