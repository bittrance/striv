class Args:
    def __init__(self, args):
        self.__dict__.update(args)


class RecordingBackend:
    def __init__(self):
        self.actions = []
        self.runs = {}

    def namespace_identity(self, driver_config):
        return hash(str(driver_config))

    def run_once(self, driver_config, jid):
        self.actions.append(('run_once', driver_config, jid))

    def sync_job(self, driver_config, jid, payload):
        self.actions.append(('sync', driver_config, jid, payload))

    def fetch_runs(self, _, job_ids):
        self.actions.append(('refresh-runs', job_ids))
        return self.runs


class RecordingLogstore:
    def __init__(self):
        self.actions = []
        self.logs = {}

    def fetch_logs(self, driver_config, run_id, run):
        self.actions.append(('fetch_logs', driver_config, run_id, run))
        if isinstance(self.logs, Exception):
            raise self.logs  # pylint: disable = raising-bad-type
        return self.logs
