# pylint: disable = missing-class-docstring, missing-function-docstring, no-self-use, redefined-outer-name
import bottle
import pytest
import webtest

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import striv_app, sqlite_store

bottle.debug(True)

AN_EXECUTION = {
    'name': 'Production Nomad',
    'driver': 'nomad',
    'driver_config': {'some': 'config'},
    'default_params': {'ze_param': 'execution'},
    'payload_template': '"ze_template"'
}

A_DIMENSION = {
    'name': 'maturity',
    'priority': 10,
    'values': {
        'operational': {
            'params': {'ze_param': 'dimension'}
        },
    }
}

A_JOB = {
    'name': 'ze-name',
    'execution': 'nomad',
    'dimensions': {
            'maturity': 'operational',
    }
}


class RecordingBackend:
    def __init__(self):
        self.actions = []

    def sync_job(self, driver_config, jid, payload):
        self.actions.append(('sync', driver_config, jid, payload))


@pytest.fixture()
def app():
    striv_app.store = sqlite_store
    striv_app.backend = RecordingBackend()
    return webtest.TestApp(striv_app.app)


@pytest.fixture()
def basicdb():
    sqlite_store.setup()
    sqlite_store.store_entity('execution', 'nomad', AN_EXECUTION)
    sqlite_store.store_entity('dimension', 'maturity', A_DIMENSION)


@pytest.mark.usefixtures('basicdb')
class TestCreateJob:
    def test_create_job_stores_the_job(self, app):
        response = app.post_json('/jobs', A_JOB)
        eid = response.json['id']
        assert eid
        created_job, *_ = sqlite_store.load_entities(('job', eid))
        assert A_JOB == created_job

    def test_create_job_invokes_backend(self, app):
        response = app.post_json('/jobs', A_JOB)
        eid = response.json['id']
        assert striv_app.backend.actions == [
            ('sync', {'some': 'config'}, eid, '"ze_template"\n')
        ]

    def test_create_job_rejects_invalid_input_with_detailed_error(self, app):
        invalid_job = A_JOB.copy()
        invalid_job.update({'gunk': False})
        response = app.post_json('/jobs', invalid_job, status=422)
        assert response.json == {'gunk': ['Unknown field.']}
