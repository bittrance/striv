import json

import botocore
import boto3

s3 = None
bucket = None
logstore = None


def _is_done(run):
    return run['status'] in ['failed', 'successful']


def setup(child_logstore, archive_config):
    global bucket, logstore, s3
    bucket = archive_config['s3_archive_bucket']
    logstore = child_logstore
    s3 = boto3.client('s3')


def fetch_logs(driver_config, run_id, run):
    key = f'{run_id}'
    if _is_done(run):
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return json.load(response['Body'])
        except botocore.exceptions.ClientError as exc:
            if exc.response['Error']['Code'] != 'NoSuchKey':
                raise exc
    logs = logstore.fetch_logs(driver_config, run_id, run)
    if _is_done(run):
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(logs).encode('utf-8')
        )
    return logs
