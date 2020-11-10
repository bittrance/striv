# pylint: disable = unsubscriptable-object

import base64
import json
import logging
import sys
import urllib.parse
import uuid
from argparse import ArgumentParser
from datetime import datetime, timezone

import marshmallow
from bottle import Bottle, HTTPResponse, request, response
from striv import schemas, templating

DEFAULT_LIMIT = 1000

app = Bottle()

backends = {}
store = None
logger = logging.getLogger('striv')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(
    '%(asctime)s  [%(levelname)s] %(message)s')
)
logger.addHandler(handler)


def cors_headers(func):
    '''
    '''
    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return func(*args, **kwargs)
    return wrapper


def marshmallow_validation(func):
    '''
    Translate marshmallow validation errors to 422s
    '''
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except marshmallow.ValidationError as err:
            logger.info('Input validation failed [err=%s]', err)
            return HTTPResponse(
                body=json.dumps({
                    'title': 'Invalid fields',
                    'invalid-fields': err.messages
                }),
                status=422,
                headers={'Content-type': 'application/json'}
            )
    return wrapper


def templating_validation(func):
    '''
    Translate templating validation errors to 422s
    '''
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except templating.ValidationError as err:
            logger.info('Template evaluation failed [err=%s]', err)
            return HTTPResponse(
                body=json.dumps({
                    'title': 'jsonnet template evaluation failed',
                    'detail': err.message,
                    'source': err.source
                }),
                status=422,
                headers={'Content-type': 'application/json'}
            )
    return wrapper


app.install(cors_headers)
app.install(marshmallow_validation)
app.install(templating_validation)


def _job_to_payload(job):
    selected_dimensions = job.get('dimensions', {})
    execution, *dimensions = store.load_entities(
        ('execution', job['execution']),
        *[('dimension', name) for name in selected_dimensions.keys()]
    )
    selected_params = []
    for ((k, v), d) in zip(selected_dimensions.items(), dimensions):
        selected_params.append(
            (d['priority'], k, d['values'][v]['params'])
        )
    selected_params.sort()
    params_snippet = templating.merge_layers(
        templating.materialize_layer('default', execution['default_params']),
        *[templating.materialize_layer(name, params)
          for (_, name, params) in selected_params],
        templating.materialize_layer(job['name'], job.get('params', {}))
    )
    return execution, templating.evaluate(
        execution['payload_template'],
        params_snippet
    )


def _apply_job(job_id, job):
    execution, payload = _job_to_payload(job)
    backend = backends[execution['driver']]
    backend.sync_job(execution['driver_config'], job_id, payload)
    job['modified_at'] = datetime.now(
        timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    store.upsert_entities(('job', job_id, job))


def _encode_page_token(*rnge):
    raw = json.dumps(rnge).encode('utf-8')
    return urllib.parse.quote(base64.b64encode(raw))


def _decode_page_token(encoded):
    return json.loads(base64.b64decode(urllib.parse.unquote(encoded)))


@app.get('/jobs')
def list_jobs():
    '''
    Retrieve a list of jobs. Returns a dict mapping id to entity.
    '''
    return store.find_entities('job')


@app.post('/jobs')
def create_job():
    '''
    Create a new job. Returns a json object with the uuid of the job.
    '''
    job = schemas.Job().load(request.json)
    job_id = str(uuid.uuid4())
    _apply_job(job_id, job)
    return {'id': job_id}


@app.post('/jobs/evaluate')
def evaluate_job():
    '''
    Evaluates a job definition, verifying that it is complete. Returns
    the payload for debugging.
    '''
    job = schemas.Job().load(request.json)
    return {'payload': _job_to_payload(job)[1]}


@app.get('/job/:job_id')
def get_job(job_id):
    '''
    Retrieve a single job definition.
    '''
    try:
        return store.load_entities(('job', job_id))[0]
    except KeyError:
        return HTTPResponse(status=404)


@app.put('/job/:job_id')
def put_job(job_id):
    '''
    Update an existing job definition. This method cannot be used to
    create new jobs.
    '''
    try:
        store.load_entities(('job', job_id))[0]
    except KeyError:
        return HTTPResponse(status=404)
    job = schemas.Job().load(request.json)
    _apply_job(job_id, job)
    return {'id': job_id}


@app.post('/runs/refresh-all')
def refresh_runs():
    '''
    Request run updates from all backend systems. Runs will be created
    and updated as necessary. Returns metrics on created and updated
    runs.
    '''
    identities = {}
    for execution in store.find_entities('execution').values():
        backend = backends[execution['driver']]
        identity = backend.namespace_identity(
            execution['driver_config']
        )
        identities[identity] = (backend, execution['driver_config'])
    jobs = store.find_entities('job')
    total_runs = 0
    for (_backend, driver_config) in identities.values():
        runs = _backend.fetch_runs(driver_config, jobs).items()
        for _, run in runs:
            run['execution'] = jobs[run['job_id']]['execution']
        store.upsert_entities(*(('run', run_id, run) for run_id, run in runs))
        total_runs += len(runs)
    return {'processed': total_runs}


@app.get('/runs')
def list_runs():
    '''
    Retrieve runs. Number of runs can be controlled by limit, but there
    is a hard max (1000 by default). If there are more runs than limit
    allows, a Link header is returned which can be used to request the
    next page.
    '''
    rnge = ['desc', None, None]
    if ('lower' in request.query or 'upper' in request.query):
        if 'page_token' in request.query:
            return HTTPResponse(
                status=400,
                body=json.dumps({
                    'title': 'pagination cannot be combined with range'
                })
            )
        rnge = ['desc', request.query.get('lower'), request.query.get('upper')]
    elif 'page_token' in request.query:
        rnge = _decode_page_token(request.query['page_token'])
    limit = int(request.query.get('limit', DEFAULT_LIMIT))
    limit = min(limit, DEFAULT_LIMIT) + 1

    runs = store.find_entities('run', range=rnge, limit=limit)
    if len(runs) == limit:
        (_, last_run) = runs.popitem()
        response.headers['Link'] = '</runs?page_token=%s>; rel="next"' % (
            _encode_page_token('desc', None, last_run['created_at'])
        )
    return runs


@app.get('/state')
def dump_state():
    '''
    Returns a json object with all config level information suitable for
    posting to /state. The dump is guaranteed to be internally
    consistent and in order to guarantee this, writes may fail during
    dumping.
    '''
    return {
        'dimensions': store.find_entities('dimension'),
        'executions': store.find_entities('execution')
    }


@app.post('/state')
def load_state():
    '''
    Replace all executions and/or dimensions in the state with those
    passed in. The payload is supposed to be a json object on the format
    {"executions": [{...}, ...], "dimensions": [{...}, ...]}. Include
    only the types that you want to replace. The load operation is
    guaranteed to be atomic, but not instantaneous (i.e. other endpoints may
    temporarily 500).
    '''
    state = schemas.State().load(request.json)
    changes = {}
    if 'dimensions' in state.keys():
        deleted, inserted = store.replace_type(
            'dimension',
            state['dimensions']
        )
        changes['dimensions'] = {'deleted': deleted, 'inserted': inserted}
    if 'executions' in state.keys():
        deleted, inserted = store.replace_type(
            'execution',
            state['executions']
        )
        changes['executions'] = {'deleted': deleted, 'inserted': inserted}
    return changes


def main():
    '''
    Developer entrypoint.
    '''
    parser = ArgumentParser(
        description='Start striv with auto reload and debug')
    parser.add_argument('--bottle-host', default='localhost',
                        help="'0.0.0.0' for ALL interfaces")
    parser.add_argument('--bottle-port', default=8080)
    parser.add_argument('--database', default=':memory:',
                        help="SQLite db file")
    parser.add_argument('--log-level', default='WARNING',
                        help='One of DEBUG, INFO, WARNING or ERROR')
    args = parser.parse_args()

    logger.setLevel(args.log_level)

    from striv import nomad_backend, sqlite_store  # pylint: disable = import-outside-toplevel
    global store, backends
    store = sqlite_store
    backends['nomad'] = nomad_backend
    store.setup(
        database=args.database,
        sortkeys={
            'job': lambda job: job['name'],
            'run': lambda run: run['created_at']
        }
    )
    app.run(host=args.bottle_host, reloader=True,
            port=args.bottle_port, debug=True)


if __name__ == '__main__':
    main()
