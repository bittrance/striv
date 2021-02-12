import itertools
import requests

from striv import errors


def _endpoint(driver_config, path):
    return '%s/%s' % (driver_config['nomad_url'], path)


def _get_tasks(driver_config, run_id):
    response = requests.get(
        _endpoint(driver_config, 'v1/allocation/%s' % run_id)
    )
    if response.status_code != requests.codes['ok']:
        raise errors.RunNotFound(response.text)
    return response.json()['TaskStates'].keys()


def _get_log(driver_config, run_id, task, typ, origin='end', offset=None):
    response = requests.get(
        _endpoint(driver_config, 'v1/client/fs/logs/%s' % run_id),
        params={
            'task': task,
            'type': typ,
            'origin': 'end',
            'offset': offset,
            'plain': 'true'
        }
    )
    if response.status_code != requests.codes['ok']:
        raise errors.RunNotFound(response.text)
    return response.text


def fetch_log_summary(driver_config, run_id):
    '''
    Retrieve the tails of all logs for a run.
    '''
    tasks = _get_tasks(driver_config, run_id)
    logs = {}
    for task, typ in itertools.product(tasks, ['stdout', 'stderr']):
        logname = '%s/%s' % (task, typ)
        try:
            logs[logname] = _get_log(
                driver_config, run_id, task, typ, offset=2000)
        except errors.RunNotFound as err:
            logs[logname] = 'fetching log failed: %s' % err
    return logs


def fetch_log(driver_config, run_id, logname):
    '''
    Retrieve the full log file for a run. The file is identified by the logname
    as seen in the keys returned by fetch_log_summary.
    '''
    task, typ = logname.rsplit('/', 2)
    return _get_log(driver_config, run_id, task, typ, origin='start')
