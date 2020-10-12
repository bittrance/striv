# pylint: disable = missing-function-docstring, redefined-outer-name

import json
import pytest
import requests_mock

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import nomad_backend

DRIVER_CONFIG = {
    'nomad_url': 'http://localhost'
}

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
