import json

import botocore
import boto3

from . import is_done, trim_logs

s3 = None
bucket = None
logstore = None


def setup(child_logstore, archive_config):
    global bucket, logstore, s3
    bucket = archive_config['s3_archive_bucket']
    logstore = child_logstore
    s3 = boto3.client('s3')


def fetch_logs(driver_config, run_id, run, max_size=None):
    key = f'{run_id}'
    if is_done(run):
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            return trim_logs(json.load(response['Body']), max_size)
        except botocore.exceptions.ClientError as exc:
            if exc.response['Error']['Code'] != 'NoSuchKey':
                raise exc
    logs = logstore.fetch_logs(driver_config, run_id, run)
    if is_done(run):
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(logs).encode('utf-8')
        )
    return trim_logs(logs, max_size)
