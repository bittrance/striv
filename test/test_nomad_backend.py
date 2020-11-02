# pylint: disable = missing-function-docstring, protected-access, redefined-outer-name

import json
import pytest
import requests_mock

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import nomad_backend
from . import nomad_allocs

DRIVER_CONFIG = {
    'nomad_url': 'http://localhost'
}

ALLOCS_ENDPOINT = DRIVER_CONFIG['nomad_url'] + '/v1/allocations'
JOBS_ENDPOINT = DRIVER_CONFIG['nomad_url'] + '/v1/job/ze-id'


@pytest.fixture
def backend():
    return nomad_backend


@pytest.fixture
def nomad():
    with requests_mock.Mocker() as mock:
        yield mock


def test_sync_job_calls_nomad(backend, nomad):
    nomad.post(JOBS_ENDPOINT, json='ok')
    payload = json.dumps({'name': 'ze-job'})
    backend.sync_job(DRIVER_CONFIG, 'ze-id', payload)
    body = json.loads(nomad.last_request.body)['Job']
    assert_that(body, has_entries(ID='ze-id', name='ze-job'))


def test_sync_job_returns_state(backend, nomad):
    nomad.post(JOBS_ENDPOINT, json='state')
    payload = json.dumps({'name': 'ze-job'})
    result = backend.sync_job(DRIVER_CONFIG, 'ze-id', payload)
    assert result == 'state'


def test_sync_job_propagates_error(backend, nomad):
    nomad.post(JOBS_ENDPOINT, status_code=500, text='BOOM')
    payload = json.dumps({'name': 'ze-job'})
    assert_that(
        calling(backend.sync_job)
        .with_args(DRIVER_CONFIG, 'ze-id', payload),
        raises(RuntimeError, pattern='BOOM')
    )


def test_extract_run_extracts_pending(backend):
    run = backend._extract_run(nomad_allocs.pending_alloc)
    assert run == {
        'created_at': '2020-10-31T23:40:00+0000',
        'status': 'pending'
    }


def test_extract_run_extracts_running(backend):
    run = backend._extract_run(nomad_allocs.running_alloc)
    assert run == {
        'created_at': '2020-10-31T23:40:00+0000',
        'started_at': '2020-10-31T23:40:02+0000',
        'status': 'running'
    }


def test_extract_run_extracts_successful(backend):
    run = backend._extract_run(nomad_allocs.successful_alloc)
    assert run == {
        'created_at': '2020-10-31T23:40:00+0000',
        'started_at': '2020-10-31T23:40:02+0000',
        'finished_at': '2020-10-31T23:40:05+0000',
        'status': 'successful'
    }


def test_extract_run_extracts_failed(backend):
    run = backend._extract_run(nomad_allocs.failed_alloc)
    assert run == {
        'created_at': '2020-10-31T23:40:00+0000',
        'started_at': '2020-10-31T23:40:02+0000',
        'finished_at': '2020-10-31T23:40:05+0000',
        'status': 'failed'
    }


def test_fetch_runs(backend, nomad):
    allocs = [
        nomad_allocs.pending_alloc,
        nomad_allocs.running_alloc,
        nomad_allocs.failed_alloc
    ]
    nomad.get(ALLOCS_ENDPOINT, json=allocs)
    runs = backend.fetch_runs(DRIVER_CONFIG, ['job-1', 'job-5'])
    assert runs.keys() == {'alloc-1', 'alloc-5'}
    assert runs['alloc-1']['job_id'] == 'job-1'
    assert runs['alloc-1']['created_at'] == '2020-10-31T23:40:00+0000'


def test_fetch_runs_accept_dict_and_set(backend, nomad):
    allocs = [
        nomad_allocs.pending_alloc,
        nomad_allocs.running_alloc,
    ]
    nomad.get(ALLOCS_ENDPOINT, json=allocs)
    assert backend.fetch_runs(DRIVER_CONFIG, {'job-1'}).keys() == {'alloc-1'}
    assert backend.fetch_runs(
        DRIVER_CONFIG, {'job-1': 1}).keys() == {'alloc-1'}
