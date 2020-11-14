# pylint: disable = missing-class-docstring, missing-function-docstring, no-self-use, redefined-outer-name, too-few-public-methods
import re
from datetime import datetime

import bottle
import pytest
import webtest

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import errors, striv_app, sqlite_store

bottle.debug(True)

AN_EXECUTION = {
    'name': 'Production Nomad',
    'driver': 'nomad',
    'logstore': 'nomad',
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


class RecordingLogstore:
    def __init__(self):
        self.actions = []
        self.logs = {}

    def fetch_logs(self, driver_config, run_id):
        self.actions.append(('fetch_logs', driver_config, run_id))
        if isinstance(self.logs, Exception):
            raise self.logs  # pylint: disable = raising-bad-type
        return self.logs


@pytest.fixture()
def backend():
    return RecordingBackend()


@pytest.fixture()
def logstore():
    return RecordingLogstore()


@pytest.fixture()
def app(backend, logstore):
    striv_app.store = sqlite_store
    striv_app.backends['nomad'] = backend
    striv_app.logstores['nomad'] = logstore
    return webtest.TestApp(striv_app.app)


@pytest.fixture()
def basicdb():
    sqlite_store.setup(
        relations={
            'run': lambda run: [('job', run['job_id'])],
            'job': lambda job: [('dvalue', '%s:%s' % (n, v)) for (n, v) in job.get('dimensions', {}).items()]
        },
        sortkeys={
            'job': lambda job: job.get('name', None),
            'run': lambda run: run.get('created_at', None)
        }
    )
    sqlite_store.upsert_entities(('execution', 'nomad', AN_EXECUTION))
    sqlite_store.upsert_entities(('dimension', 'maturity', A_DIMENSION))


@pytest.fixture()
def four_runs():
    sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
    sqlite_store.upsert_entities(('job', 'job-2', A_JOB))
    sqlite_store.upsert_entities(('run', 'run-1', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:00+0000',
    }))
    sqlite_store.upsert_entities(('run', 'run-2', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:01+0000',
    }))
    sqlite_store.upsert_entities(('run', 'run-3', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:02+0000',
    }))
    sqlite_store.upsert_entities(('run', 'run-4', {
        'job_id': 'job-2',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:03+0000',
    }))


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

    def test_ignores_readonly_modified_at(self, app):
        job = A_JOB.copy()
        job['modified_at'] = '2020-10-31T23:40:40+0000'
        app.post_json('/jobs/evaluate', job)

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
        assert created_job['name'] == 'ze-name'
        assert datetime.strptime(
            created_job['modified_at'],
            '%Y-%m-%dT%H:%M:%S%z'
        ).timestamp() - datetime.now().timestamp() < 1

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
        stored_job = sqlite_store.load_entities(('job', 'job-1'))[0]
        assert stored_job['name'] == 'updated'

    def test_ignores_readonly_modified_at(self, app):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        updated_job = A_JOB.copy()
        updated_job['modified_at'] = '2020-10-31T23:40:00+0000'
        app.put_json('/job/job-1', updated_job)
        stored_job = sqlite_store.load_entities(('job', 'job-1'))[0]
        assert stored_job['modified_at'] != '2020-10-31T23:40:00+0000'

    def test_put_job_maintains_modified_at(self, app):
        job = A_JOB.copy()
        job['modified_at'] = '2020-10-31T23:40:00+0000'
        sqlite_store.upsert_entities(('job', 'job-1', job))
        assert app.put_json('/job/job-1', A_JOB).json == {'id': 'job-1'}
        stored_job = sqlite_store.load_entities(('job', 'job-1'))[0]
        assert stored_job['modified_at'] > '2020-10-31T23:40:00+0000'

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


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestListJobRuns:
    def test_returns_job_for_one_run(self, app):
        response = app.get('/job/job-1/runs')
        assert response.json.keys() == {'run-1', 'run-2', 'run-3'}
        response = app.get('/job/job-2/runs')
        assert response.json.keys() == {'run-4'}

    def test_returns_404_for_unknown_job(self, app):
        app.get('/job/job-3/runs', status=404)

    def test_accepts_limit_and_returns_youngest_first(self, app):
        response = app.get('/job/job-1/runs?limit=2')
        assert response.json.keys() == {'run-3', 'run-2'}

    def test_respects_paginates(self, app):
        response = app.get('/job/job-1/runs?limit=2')
        assert_that(
            response.headers['link'],
            matches_regexp('<(.*)>; rel="next"')
        )
        url = re.match('<(.*)>; rel="next"', response.headers['link'])[1]
        response = app.get(url + '&limit=2')
        assert response.json.keys() == {'run-1'}
        assert not response.headers.get('link')

    def test_accepts_range(self, app):
        response = app.get('/job/job-1/runs', {
            'lower': '2020-10-31T23:40:00+0000',
            'upper': '2020-10-31T23:40:01+0000',
        })
        assert response.json.keys() == {'run-2', 'run-1'}

    def test_refuses_range_and_page_token(self, app):
        app.get('/runs', {'lower': 'asdf', 'page_token': 'asdf'}, status=400)


@pytest.mark.usefixtures('basicdb')
class TestRefreshRuns:
    def test_creates_runs_for_all_executions(self, app, backend):
        sqlite_store.upsert_entities(('job', 'job-1', A_JOB))
        backend.runs['alloc-1'] = A_RUN
        response = app.post('/runs/refresh-all')
        runs = sqlite_store.find_entities('run')
        assert_that(runs['alloc-1'], has_entries({
            'job_id': 'job-1',
            'execution': 'nomad'
        }))
        assert response.json == {'processed': 1}


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestListRuns:
    def test_returns_all_runs(self, app):
        response = app.get('/runs')
        assert response.json.keys() == {
            'run-1', 'run-2', 'run-3', 'run-4'}

    def test_accepts_limit_and_returns_youngest_first(self, app):
        response = app.get('/runs?limit=2')
        assert response.json.keys() == {'run-3', 'run-4'}

    def test_respects_paginates(self, app):
        response = app.get('/runs?limit=2')
        assert_that(
            response.headers['link'],
            matches_regexp('<(.*)>; rel="next"')
        )
        url = re.match('<(.*)>; rel="next"', response.headers['link'])[1]
        response = app.get(url + '&limit=2')
        assert response.json.keys() == {'run-1', 'run-2'}
        assert not response.headers.get('link')

    def test_accepts_range(self, app):
        response = app.get('/runs', {
            'limit': 2,
            'lower': '2020-10-31T23:40:01+0000',
            'upper': '2020-10-31T23:40:02+0000',
        })
        assert response.json.keys() == {'run-2', 'run-3'}

    def test_refuses_range_and_page_token(self, app):
        app.get('/runs', {'lower': 'asdf', 'page_token': 'asdf'}, status=400)


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestGetRun:
    def test_retrieves_single_run(self, app):
        assert app.get('/run/run-1').json['job_id'] == 'job-1'

    def test_returns_404_on_nonexistent_job(self, app):
        app.get('/run/nonsense', status=404)


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestGetRunLog:
    def test_invokes_logstore(self, app, logstore):
        logstore.logs = {'run-1/stderr': 'ze-logs'}
        app.get('/run/run-1/logs')
        assert logstore.actions == [
            ('fetch_logs', {'some': 'config'}, 'run-1')
        ]

    def test_returns_logs(self, app, logstore):
        logstore.logs = {'run-1/stderr': 'ze-log'}
        response = app.get('/run/run-1/logs')
        assert response.json == {'run-1/stderr': 'ze-log'}

    def test_says_run_is_gone(self, app, logstore):
        logstore.logs = errors.RunNotFound('boom!')
        app.get('/run/run-1/logs', status=410)


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
