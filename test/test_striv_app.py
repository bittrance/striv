# pylint: disable = missing-class-docstring, missing-function-docstring, no-self-use, redefined-outer-name, too-few-public-methods
import json
import re
from datetime import datetime

import bottle
import pytest
import webtest
from hamcrest import *  # pylint: disable = unused-wildcard-import

from . import rdbm_support, utils
from striv import crypto, errors, striv_app


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
    'job_id': 'job-1',
    'created_at': '2020-10-31T23:40:00+0000',
}


@pytest.fixture()
def backend():
    return utils.RecordingBackend()


@pytest.fixture()
def logstore():
    return utils.RecordingLogstore()


@pytest.fixture(params=rdbm_support.configurations)
def app(request, backend, logstore):
    driver, connargs = request.param
    args = utils.Args(
        archive_config={},
        log_level='DEBUG',
        store_type=driver,
        store_config=json.dumps(connargs),
        encryption_key=crypto.generate_key(),
    )
    striv_app.configure(striv_app.app, args)
    striv_app.app.backends['nomad'] = backend
    striv_app.app.logstores['nomad'] = logstore
    return webtest.TestApp(striv_app.app)


@pytest.fixture()
def basicdb(app):
    app.app.store.upsert_entities(('execution', 'nomad', AN_EXECUTION))
    app.app.store.upsert_entities(('dimension', 'maturity', A_DIMENSION))
    yield
    # TODO: Teach replace_type about relations
    app.app.store.CONN.cursor().execute('DELETE FROM entities')
    app.app.store.CONN.cursor().execute('DELETE FROM relations')


@pytest.fixture()
def four_runs(app):
    app.app.store.upsert_entities(('job', 'job-1', A_JOB))
    app.app.store.upsert_entities(('job', 'job-2', A_JOB))
    app.app.store.upsert_entities(('run', 'run-1', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:00+0000',
    }))
    app.app.store.upsert_entities(('run', 'run-2', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:01+0000',
    }))
    app.app.store.upsert_entities(('run', 'run-3', {
        'job_id': 'job-1',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:02+0000',
    }))
    app.app.store.upsert_entities(('run', 'run-4', {
        'job_id': 'job-2',
        'execution': 'nomad',
        'created_at': '2020-10-31T23:40:03+0000',
    }))


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestListJobs:
    def test_list_jobs(self, app):
        response = app.get('/jobs')
        assert response.json.keys() == {'job-1', 'job-2'}


@pytest.mark.usefixtures('basicdb')
class TestEvaluateJob:
    def test_returns_expanded_payload(self, app):
        response = app.post_json('/jobs/evaluate', A_JOB)
        assert_that(response.json, has_entry('payload', '"ze_template"\n'))

    def test_returns_effective_parameters(self, app):
        response = app.post_json('/jobs/evaluate', A_JOB)
        assert_that(
            response.json,
            has_entry('params', {'ze_param': 'execution'})
        )

    def test_redacts_secrets(self, app):
        execution = AN_EXECUTION.copy()
        execution['payload_template'] = 'params.param'
        app.app.store.upsert_entities(('execution', 'nomad', execution))
        job = A_JOB.copy()
        job['params'] = {
            'param': {'_striv_type': 'secret', 'encrypted': 'verrah-secret'}
        }
        response = app.post_json('/jobs/evaluate', job)
        assert_that(response.json, has_entry('payload', '"<redacted>"\n'))

    def test_ignores_readonly_modified_at(self, app):
        job = A_JOB.copy()
        job['modified_at'] = '2020-10-31T23:40:40+0000'
        app.post_json('/jobs/evaluate', job)

    def test_evaluate_job_explains_why_template_is_invalid(self, app):
        bad_execution = AN_EXECUTION.copy()
        bad_execution.update({'payload_template': '"foo'})
        app.app.store.upsert_entities(
            ('execution', 'bad_nomad', bad_execution))
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
        created_job, *_ = app.app.store.load_entities(('job', eid))
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

    def test_passes_decrypted_secret_to_backend(self, app, backend):
        execution = AN_EXECUTION.copy()
        execution['payload_template'] = 'params.param'
        app.app.store.upsert_entities(('execution', 'nomad', execution))
        job = A_JOB.copy()
        job['params'] = {
            'param': {
                '_striv_type': 'secret',
                'encrypted': crypto.encrypt_value(app.app.public_key_pem, 'verrah-secret')
            }
        }
        app.post_json('/jobs', job)
        assert backend.actions[0][3] == '"verrah-secret"\n'

    def test_explodes_on_invalid_encryption(self, app, backend):
        unknown_key = crypto.recover_pubkey(
            crypto.deserialize_private_key(crypto.generate_key()))
        job = A_JOB.copy()
        job['params'] = {
            'param': {
                '_striv_type': 'secret',
                'encrypted': crypto.encrypt_value(unknown_key, 'verrah-secret')
            }
        }
        response = app.post_json('/jobs', job, status=422)
        assert_that(
            response.json,
            has_entry('source', has_entry('_striv_type', 'secret'))
        )

    def test_create_job_rejects_invalid_input_with_detailed_error(self, app):
        invalid_job = A_JOB.copy()
        invalid_job.update({'gunk': False})
        response = app.post_json('/jobs', invalid_job, status=422)
        assert response.json['invalid-fields'] == {'gunk': ['Unknown field.']}

    def test_create_job_rejects_broken_template_with_detailed_error(self, app):
        bad_execution = AN_EXECUTION.copy()
        bad_execution.update({'payload_template': '"foo'})
        app.app.store.upsert_entities(
            ('execution', 'bad_nomad', bad_execution))
        job = A_JOB.copy()
        job.update({'execution': 'bad_nomad'})
        response = app.post_json('/jobs', job, status=422)
        assert_that(response.json['detail'], matches_regexp('unterminated'))


@pytest.mark.usefixtures('basicdb')
class TestGetJob:
    def test_get_job_retrieves_single_job(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        assert app.get('/job/job-1').json == A_JOB

    def test_get_job_returns_404_on_nonexistent_job(self, app):
        app.get('/job/nonsense', status=404)

    def test_returns_invalid_id(self, app):
        response = app.get('/job/nonsense', expect_errors=True)
        assert_that(response.json, has_entry('entity_id', 'job:nonsense'))


@pytest.mark.usefixtures('basicdb')
class TestPutJob:
    def test_put_job_overwrites_single_job(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        updated_job = A_JOB.copy()
        updated_job['name'] = 'updated'
        assert app.put_json(
            '/job/job-1', updated_job).json == {'id': 'job-1'}
        stored_job = app.app.store.load_entities(('job', 'job-1'))[0]
        assert stored_job['name'] == 'updated'

    def test_ignores_readonly_modified_at(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        updated_job = A_JOB.copy()
        updated_job['modified_at'] = '2020-10-31T23:40:00+0000'
        app.put_json('/job/job-1', updated_job)
        stored_job = app.app.store.load_entities(('job', 'job-1'))[0]
        assert stored_job['modified_at'] != '2020-10-31T23:40:00+0000'

    def test_put_job_maintains_modified_at(self, app):
        job = A_JOB.copy()
        job['modified_at'] = '2020-10-31T23:40:00+0000'
        app.app.store.upsert_entities(('job', 'job-1', job))
        assert app.put_json('/job/job-1', A_JOB).json == {'id': 'job-1'}
        stored_job = app.app.store.load_entities(('job', 'job-1'))[0]
        assert stored_job['modified_at'] > '2020-10-31T23:40:00+0000'

    def test_put_job_invokes_backend(self, app, backend):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        app.put_json('/job/job-1', A_JOB)
        assert backend.actions == [
            ('sync', {'some': 'config'}, 'job-1', '"ze_template"\n')
        ]

    def test_put_job_returns_404_on_nonexistent_job(self, app):
        app.put_json('/job/nonsense', {}, status=404)

    def test_put_job_rejects_invalid_input_with_detailed_error(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        invalid_job = A_JOB.copy()
        invalid_job.update({'gunk': False})
        response = app.put_json('/job/job-1', invalid_job, status=422)
        assert response.json['invalid-fields'] == {'gunk': ['Unknown field.']}


class TestDeleteJob:
    def test_deletes_job(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        app.delete('/job/job-1')
        assert app.app.store.find_entities('job') == {}

    def test_returns_id(self, app):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        response = app.delete('/job/job-1')
        assert response.json['id'] == 'job-1'

    def test_returns_404_on_nonexistent_job(self, app):
        app.delete('/job/job-1', status=404)


@pytest.mark.usefixtures('basicdb', 'four_runs')
class TestRunJobNow:
    def test_invoke_backend(self, app, backend):
        app.post('/job/job-1/run-now')
        assert backend.actions == [('run_once', {'some': 'config'}, 'job-1')]

    def test_returns_404_for_unknown_job(self, app):
        app.post('/job/job-3/run-now', status=404)


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


class TestPublicKey:
    def test_returns_public_key(self, app):
        response = app.get('/public-key')
        assert 'BEGIN PUBLIC KEY' in response.json['public-key']

    def test_without_key_returns_501(self, app):
        app.app.public_key_pem = None
        app.get('/public-key', status=501)


@pytest.mark.usefixtures('basicdb')
class TestRefreshRuns:
    def test_creates_runs_for_all_executions(self, app, backend):
        app.app.store.upsert_entities(('job', 'job-1', A_JOB))
        backend.runs['alloc-1'] = A_RUN
        response = app.post('/runs/refresh-all')
        runs = app.app.store.find_entities('run')
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
            ('fetch_logs', {'some': 'config'}, 'run-1', A_RUN, {})
        ]

    def test_returns_logs(self, app, logstore):
        logstore.logs = {'run-1/stderr': 'ze-log'}
        response = app.get('/run/run-1/logs')
        assert response.json == {'run-1/stderr': 'ze-log'}

    def test_says_run_is_gone_in_json(self, app, logstore):
        logstore.logs = errors.RunNotFound('boom!')
        response = app.get('/run/run-1/logs', status=410)
        assert response.json['detail'] == 'boom!'

    def test_propagates_max_size(self, app, logstore):
        logstore.logs = {'run-1/stderr': 'ze-logs'}
        app.get('/run/run-1/logs?max_size=10')
        assert logstore.actions == [
            ('fetch_logs', {'some': 'config'},
             'run-1', A_RUN, {'max_size': 10})
        ]


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
            calling(app.app.store.load_entities)
            .with_args(('dimension', 'maturity')),
            raises(errors.EntityNotFound)
        )
        assert app.app.store.load_entities(
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
            calling(app.app.store.load_entities)
            .with_args(('execution', 'nomad')),
            raises(errors.EntityNotFound)
        )
        assert app.app.store.load_entities(
            ('execution', 'another-execution')
        ) == [AN_EXECUTION]
