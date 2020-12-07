import itertools
from datetime import datetime, timezone
import json
import requests


def _endpoint(driver_config, path):
    return '%s/%s' % (driver_config['nomad_url'], path)


def _parse_nomad_ts(ts):
    return datetime.fromtimestamp(
        ts / 1000000000,
        tz=timezone.utc
    ).strftime('%Y-%m-%dT%H:%M:%S%z')


def _extract_start_time(alloc):
    if 'TaskStates' not in alloc:
        return None
    events = itertools.chain(
        *[task['Events'] for task in alloc['TaskStates'].values()]
    )
    starts = sorted((e['Time'] for e in events if e['Type'] == 'Started'))
    return _parse_nomad_ts(starts[0]) if len(starts) > 0 else None


def _extract_run(alloc):
    run = {
        'created_at': _parse_nomad_ts(alloc['CreateTime']),
    }
    started_at = _extract_start_time(alloc)
    if alloc['ClientStatus'] == 'failed':
        run['status'] = 'failed'
        run['started_at'] = started_at
        run['finished_at'] = _parse_nomad_ts(alloc['ModifyTime'])
    elif alloc['ClientStatus'] == 'complete':
        run['status'] = 'successful'
        run['started_at'] = started_at
        run['finished_at'] = _parse_nomad_ts(alloc['ModifyTime'])
    elif started_at:
        run['status'] = 'running'
        run['started_at'] = started_at
    else:
        run['status'] = 'pending'

    return run


def namespace_identity(driver_config):
    '''
    Returns an opaque identifier which identifies an executing
    system. This identifier is used to verify that we are not putting
    identical queries to the same executing system multiple times just
    because there are multiple executions pointing towards the same
    cluster. This is currently calculated using nomad_url, but should
    really take namespaces into account.
    '''
    return hash(driver_config['nomad_url'])


def run_once(driver_config, jid):
    '''
    Run the periodic job specified by jid now.
    '''
    response = requests.post(
        _endpoint(driver_config, 'v1/job/%s/periodic/force' % jid)
    )
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)


def sync_job(driver_config, jid, payload):
    '''
    Create or update a Nomad job. jid will be used as Nomad job id.
    '''
    payload = {'Job': json.loads(payload)}
    payload['Job']['ID'] = jid
    response = requests.post(
        _endpoint(driver_config, 'v1/job/' + jid),
        json=payload
    )
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)
    return response.json()


def fetch_runs(driver_config, job_ids):
    '''
    Retrieve a dictionary mapping job_ids to known runs for those jobs.
    For large job_ids lists, please pass in a set.
    '''
    response = requests.get(_endpoint(driver_config, 'v1/allocations'))
    if response.status_code != requests.codes['ok']:
        raise RuntimeError(response.text)
    runs = {}
    for alloc in response.json():
        job_id, *_ = alloc['JobID'].split('/')  # periodic jobs have a suffix
        if job_id in job_ids:
            run_id = alloc['ID']
            run = _extract_run(alloc)
            run['job_id'] = job_id
            runs[run_id] = run
    return runs
