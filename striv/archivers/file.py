import json
import os.path

from . import is_done, trim_logs

archive_dir = None
logstore = None


def _archive(run_id):
    path = f'{run_id}.json'
    return os.path.join(archive_dir, path)


def setup(child_logstore, archive_config):
    global archive_dir, logstore
    archive_dir = archive_config['archive_dir']
    logstore = child_logstore


def fetch_logs(driver_config, run_id, run, max_size=None):
    path = _archive(run_id)
    if is_done(run):
        if os.path.exists(path):
            with open(path) as f:
                return trim_logs(json.load(f), max_size)
    logs = logstore.fetch_logs(
        driver_config, run_id, run
    )
    if is_done(run):
        with open(path, 'w') as f:
            json.dump(logs, f)
    return trim_logs(logs, max_size)
