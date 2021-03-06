import json
import os.path

archive_dir = None
logstore = None


def _archive(run_id):
    path = f'{run_id}.json'
    return os.path.join(archive_dir, path)


def _is_done(run):
    return run['status'] in ['failed', 'successful']


def _trim_logs(logs, max_size):
    for k in logs:
        logs[k] = logs[k][:max_size]
    return logs


def setup(child_logstore, archive_config):
    global archive_dir, logstore
    archive_dir = archive_config['archive_dir']
    logstore = child_logstore


def fetch_logs(driver_config, run_id, run, max_size=None):
    path = _archive(run_id)
    if _is_done(run):
        if os.path.exists(path):
            with open(path) as f:
                return _trim_logs(json.load(f), max_size)
    logs = logstore.fetch_logs(
        driver_config, run_id, run
    )
    if _is_done(run):
        with open(path, 'w') as f:
            json.dump(logs, f)
    return _trim_logs(logs, max_size)
