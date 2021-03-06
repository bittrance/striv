import boto3
import moto
import pytest

from . import utils
from striv.archivers import file, s3

example_logs = {'some': 'log'}


@pytest.fixture
def driver_config():
    return {}


@pytest.fixture
def pending_run():
    return {'status': 'pending'}


@pytest.fixture
def successful_run():
    return {'status': 'successful'}


@pytest.fixture
def upstream():
    logstore = utils.RecordingLogstore()
    logstore.logs = example_logs
    return logstore


class ArchiverContract:
    def test_propagating_upstream_result(self, subject, successful_run, driver_config):
        logs = subject.fetch_logs(driver_config, 'ze-id', successful_run)
        assert logs == example_logs

    def test_delegating_to_upstream(self, subject, upstream, driver_config, successful_run):
        subject.fetch_logs(driver_config, 'ze-id', successful_run)
        assert upstream.actions == [(
            'fetch_logs', driver_config, 'ze-id', successful_run, {}
        )]

    def test_does_not_pass_max_size_upstream(self, subject, upstream, driver_config, successful_run):
        subject.fetch_logs(driver_config, 'ze-id', successful_run, max_size=1)
        assert upstream.actions == [(
            'fetch_logs', driver_config, 'ze-id', successful_run, {}
        )]

    def test_enforces_max_size(self, subject, upstream, driver_config, successful_run):
        logs = subject.fetch_logs(
            driver_config, 'ze-id', successful_run, max_size=1)
        assert logs == {'some': 'l'}

    def test_caches_upstream_completed_runs(self, subject, upstream, driver_config, successful_run):
        subject.fetch_logs(driver_config, 'ze-id', successful_run)
        subject.fetch_logs(driver_config, 'ze-id', successful_run)
        assert len(upstream.actions) == 1

    def test_returns_cached_result(self, subject, driver_config, successful_run):
        subject.fetch_logs(driver_config, 'ze-id', successful_run)
        logs = subject.fetch_logs(driver_config, 'ze-id', successful_run)
        assert logs == example_logs

    def test_does_not_cache_in_progress_runs(self, subject, upstream, driver_config, pending_run):
        subject.fetch_logs(driver_config, 'ze-id',  pending_run)
        subject.fetch_logs(driver_config, 'ze-id',  pending_run)
        assert len(upstream.actions) == 2


class TestS3Archiver(ArchiverContract):
    @pytest.fixture
    def subject(self, upstream):
        with moto.mock_s3():
            boto3.client('s3').create_bucket(
                Bucket='test-bucket',
                CreateBucketConfiguration={
                    'LocationConstraint': 'us-west-2'
                }
            )
            s3.setup(upstream, {
                's3_archive_bucket': 'test-bucket',
            })
            yield s3


class TestFileArchiver(ArchiverContract):
    @pytest.fixture
    def subject(self, upstream, tmpdir):
        file.setup(upstream, {'archive_dir': tmpdir})
        yield file
