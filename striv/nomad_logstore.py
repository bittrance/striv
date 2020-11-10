import itertools
import requests

from striv import errors


def _endpoint(driver_config, path):
    return '%s/%s' % (driver_config['nomad_url'], path)


def fetch_logs(driver_config, run_id):
    '''
    Retrieve the log for a run.
    '''
    response = requests.get(
        _endpoint(driver_config, 'v1/allocation/%s' % run_id)
    )
    if response.status_code != requests.codes['ok']:
        raise errors.RunNotFound(response.text)
    tasks = response.json()['TaskStates'].keys()
    logs = {}
    for task, typ in itertools.product(tasks, ['stdout', 'stderr']):
        response = requests.get(
            _endpoint(driver_config, 'v1/client/fs/logs/%s' % run_id),
            params={
                'task': task,
                'type': typ,
                'origin': 'end',
                'offset': 64000,
                'plain': 'true'
            }
        )
        logname = '%s/%s' % (task, typ)
        if response.status_code == requests.codes['ok']:
            logs[logname] = response.text
        else:
            logs[logname] = 'fetching log failed: %s' % response.text
    return logs
