def is_done(run):
    return run['status'] in ['failed', 'successful']


def trim_logs(logs, max_size):
    for k in logs:
        logs[k] = logs[k][:max_size]
    return logs
