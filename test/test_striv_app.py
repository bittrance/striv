# pylint: disable = missing-class-docstring, missing-function-docstring, no-self-use, redefined-outer-name, too-few-public-methods
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
}

A_RUN = {
    'job_id': 'job-1'
}


class RecordingBackend:
    def __init__(self):
        self.actions = []
        self.runs = {}

    def namespace_identity(self, driver_config):
        return hash(str(driver_config))

    def sync_job(self, driver_config, jid, payload):
        self.actions.append(('sync', driver_config, jid, payload))

    def fetch_runs(self, _, job_ids):
        self.actions.append(('refresh-runs', job_ids))
        return self.runs


@pytest.fixture()
def backend():
    return RecordingBackend()


@pytest.fixture()
def app(backend):
    striv_app.store = sqlite_store
    striv_app.backends['nomad'] = backend
    return webtest.TestApp(striv_app.app)


@pytest.fixture()
def basicdb():
    sqlite_store.setup()
    sqlite_store.upsert_entities(('execution', 'nomad', AN_EXECUTION))
    sqlite_store.upsert_entities(('dimension', 'maturity', A_DIMENSION))


class TestListJobs:
    def test_list_jobs(self, app):
        sqlite_store.setup()
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        sqlite_store.upsert_entities(('job', 'job-2', A_JOB))
        response = app.get('/jobs')
        assert response.json == {'job-1': A_JOB, 'job-2': A_JOB}


@pytest.mark.usefixtures('basicdb')
class TestEvaluateJob:
    def test_evaluate_job(self, app):
        response = app.post_json('/jobs/evaluate', A_JOB)
        assert response.json == {'payload': '"ze_template"\n'}

    def test_evaluate_job_explains_why_template_is_invalid(self, app):
        bad_execution = AN_EXECUTION.copy()
        bad_execution.update({'payload_template': '"foo'})
        sqlite_store.upsert_entities(('execution', 'bad_nomad', bad_execution))
        job = A_JOB.copy()
        job.update({'execution': 'bad_nomad'})
        response = app.post_json('/jobs/evaluate', job, status=422)
        assert_that(response.json['detail'], matches_regexp('unterminated'))


@pytest.mark.usefixtures('basicdb')
class TestCreateJob:
    def test_create_job_stores_the_job(self, app):
        response = app.post_json('/jobs', A_JOB)
        eid = response.json['id']
        assert eid
        created_job, *_ = sqlite_store.load_entities(('job', eid))
        assert A_JOB == created_job

    def test_create_job_invokes_backend(self, app, backend):
        response = app.post_json('/jobs', A_JOB)
        eid = response.json['id']
        assert backend.actions == [
            ('sync', {'some': 'config'}, eid, '"ze_template"\n')
        ]

    def test_create_job_rejects_invalid_input_with_detailed_error(self, app):
        invalid_job = A_JOB.copy()
        invalid_job.update({'gunk': False})
        response = app.post_json('/jobs', invalid_job, status=422)
        assert response.json['invalid-fields'] == {'gunk': ['Unknown field.']}

    def test_create_job_rejects_broken_template_with_detailed_error(self, app):
        bad_execution = AN_EXECUTION.copy()
        bad_execution.update({'payload_template': '"foo'})
        sqlite_store.upsert_entities(('execution', 'bad_nomad', bad_execution))
        job = A_JOB.copy()
        job.update({'execution': 'bad_nomad'})
        response = app.post_json('/jobs', job, status=422)
        assert_that(response.json['detail'], matches_regexp('unterminated'))


@pytest.mark.usefixtures('basicdb')
class TestGetJob:
    def test_get_job_retrieves_single_job(self, app):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        assert app.get('/job/job-1').json == A_JOB

    def test_get_job_returns_404_on_nonexistent_job(self, app):
        app.get('/job/nonsense', status=404)


@pytest.mark.usefixtures('basicdb')
class TestPutJob:
    def test_put_job_overwrites_single_job(self, app):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        updated_job = A_JOB.copy()
        updated_job['name'] = 'updated'
        assert app.put_json(
            '/job/job-1', updated_job).json == {'id': 'job-1'}
        assert sqlite_store.load_entities(('job', 'job-1'))[0] == updated_job

    def test_put_job_invokes_backend(self, app, backend):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        app.put_json('/job/job-1', A_JOB)
        assert backend.actions == [
            ('sync', {'some': 'config'}, 'job-1', '"ze_template"\n')
        ]

    def test_put_job_returns_404_on_nonexistent_job(self, app):
        app.put_json('/job/nonsense', {}, status=404)

    def test_put_job_rejects_invalid_input_with_detailed_error(self, app):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        invalid_job = A_JOB.copy()
        invalid_job.update({'gunk': False})
        response = app.put_json('/job/job-1', invalid_job, status=422)
        assert response.json['invalid-fields'] == {'gunk': ['Unknown field.']}


@pytest.mark.usefixtures('basicdb')
class TestRefreshRuns:
    def test_creates_runs_for_all_executions(self, app, backend):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        backend.runs['alloc-1'] = A_RUN
        response = app.post('/runs/refresh-all')
        runs = sqlite_store.find_entities('run')
        assert_that(runs['alloc-1'], has_entry('job_id', 'job-1'))
        assert response.json == {'processed': 1}


class TestListRuns:
    def test_list_runs(self, app):
        sqlite_store.setup()
        sqlite_store.upsert_entities(('run', 'alloc-1', A_RUN))
        sqlite_store.upsert_entities(('run', 'alloc-2', A_RUN))
        response = app.get('/runs')
        assert response.json == {'alloc-1': A_RUN, 'alloc-2': A_RUN}


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
