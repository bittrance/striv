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
