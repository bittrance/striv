# pylint: disable = unsubscriptable-object

import uuid

from bottle import Bottle, request
from . import templating

app = Bottle()

backend = None
store = None


@app.post('/jobs')
def create_job():
    '''
    Create a new job. Returns a json object with the uuid of the job.
    '''
    job = request.json
    # TODO: validate against schema
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
