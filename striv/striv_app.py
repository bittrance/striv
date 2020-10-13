# pylint: disable = unsubscriptable-object

import uuid
from argparse import ArgumentParser

import json
import marshmallow
from bottle import Bottle, HTTPResponse, request
from striv import schemas, templating

app = Bottle()

backend = None
store = None


def marshmallow_validation(func):
    '''
    Translate marshmallow validation errors to 422s
    '''
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except marshmallow.ValidationError as err:
            return HTTPResponse(
                body=json.dumps(err.messages),
                status=422,
                headers={'Content-type': 'application/json'}
            )
    return wrapper


app.install(marshmallow_validation)


@app.post('/jobs')
def create_job():
    '''
    Create a new job. Returns a json object with the uuid of the job.
    '''
    job = schemas.Job().load(request.json)
    selected_dimensions = job['dimensions']
    execution, *dimensions = store.load_entities(
        ('execution', job['execution']),
        *[('dimension', name) for name in selected_dimensions.keys()]
    )
    selected_params = []
    for (v, d) in zip(selected_dimensions.values(), dimensions):
        selected_params.append(
            (d['priority'], d['name'], d['values'][v]['params'])
        )
    selected_params.sort()
    params_snippet = templating.merge_layers(
        templating.materialize_layer('default', execution['default_params']),
        *[templating.materialize_layer(name, params)
          for (_, name, params) in selected_params],
        templating.materialize_layer(job['name'], job.get('params', {}))
    )
    payload = templating.evaluate(
        execution['payload_template'],
        params_snippet
    )
    eid = str(uuid.uuid4())
    backend.sync_job(execution['driver_config'], eid, payload)
    store.store_entity('job', eid, job)
    return {'id': eid}


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
    args = parser.parse_args()

    from striv import nomad_backend, sqlite_store  # pylint: disable = import-outside-toplevel
    global store, backend
    store = sqlite_store
    backend = nomad_backend
    store.setup(database=args.database)
    app.run(host=args.bottle_host, reloader=True,
            port=args.bottle_port, debug=True)


if __name__ == '__main__':
    main()
