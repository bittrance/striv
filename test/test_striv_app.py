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


class TestListJobs:
    def test_list_jobs(self, app):
        sqlite_store.setup()
        sqlite_store.store_entity('job', 'job-1', A_JOB)
        sqlite_store.store_entity('job', 'job-2', A_JOB)
        response = app.get('/jobs')
        assert response.json == {'job-1': A_JOB, 'job-2': A_JOB}


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


@pytest.mark.usefixtures('basicdb')
class TestDumpState:
    def test_dump_state(self, app):
        assert app.get('/state').json == {
            'dimensions': {'maturity': A_DIMENSION},
            'executions': {'nomad': AN_EXECUTION}
        }

    def test_roundtrip(self, app):
        state = app.get('/state').json
        assert app.post_json('/state', state).json == {
            'dimensions': {'deleted': 1, 'inserted': 1},
            'executions': {'deleted': 1, 'inserted': 1}
        }


@pytest.mark.usefixtures('basicdb')
class TestLoadState:
    def test_load_state_dimensions(self, app):
        state = {
            'dimensions': {
                'another-maturity': A_DIMENSION
            },
        }
        response = app.post_json('/state', state)
        assert response.json == {'dimensions': {'deleted': 1, 'inserted': 1}}
        assert_that(
            calling(sqlite_store.load_entities)
            .with_args(('dimension', 'maturity')),
            raises(KeyError)
        )
        assert sqlite_store.load_entities(
            ('dimension', 'another-maturity')
        ) == [A_DIMENSION]

    def test_load_state_executions(self, app):
        state = {
            'executions': {
                'another-execution': AN_EXECUTION
            },
        }
        response = app.post_json('/state', state)
        assert response.json == {'executions': {'deleted': 1, 'inserted': 1}}
        assert_that(
            calling(sqlite_store.load_entities)
            .with_args(('execution', 'nomad')),
            raises(KeyError)
        )
        assert sqlite_store.load_entities(
            ('execution', 'another-execution')
        ) == [AN_EXECUTION]
