import pytest
from requests import status_codes
import requests_mock

from hamcrest import *  # pylint: disable = unused-wildcard-import
from striv import archivist
from . import utils

run_1 = {'status': 'running', 'created_at': '2020-10-31T23:40:02+0000'}
run_2 = {'status': 'successful', 'created_at': '2020-10-31T23:40:01+0000'}
run_3 = {'status': 'failed', 'created_at': '2020-10-31T23:40:00+0000'}
run_4 = {'status': 'running', 'created_at': '2020-10-31T23:39:00+0000'}


@pytest.fixture
def striv():
    with requests_mock.Mocker() as mock:
        yield mock


class TestRunsSince:
    def test_it_follows_link_headers(self, striv):
        striv.get(
            '/runs?lower=2020-10-31T23:40:00+0000',
            headers={'Link': '</runs?page_token=ze-token>; rel="next"'},
            json={'run-1': run_1, 'run-2': run_2}
        )
        striv.get(
            '/runs?page_token=ze-token',
            json={'run-3': run_3}
        )
        assert len(list(archivist.runs_since('http://localhost',
                                             '2020-10-31T23:40:00+0000'))) == 3

    def test_aborts_on_500(self, striv):
        striv.get('/runs', status_code=500)
        generator = archivist.runs_since(
            'http://localhost', '2020-10-31T23:40:00+0000')
        assert_that(
            calling(generator.__next__),
            raises(RuntimeError)
        )


class TestUniqueFinishedRuns:
    def test_run_reported_only_when_finished(self):
        filter = archivist.UniqueFinishedRuns()
        assert list(filter.process([('run-1', run_1)])) == []
        assert list(filter.process([('run-1', run_2)])) == [('run-1', run_2)]

    def test_emits_finished_run_once(self):
        filter = archivist.UniqueFinishedRuns()
        assert list(filter.process([('run-2', run_2)])) == [('run-2', run_2)]
        assert list(filter.process([('run-2', run_2)])) == []

    def test_finished_runs_are_pruned_from_memory(self):
        filter = archivist.UniqueFinishedRuns()
        output = list(filter.process([('run-2', run_2), ('run-3', run_3)]))
        assert len(output) == 2
        filter.prune('2020-10-31T23:40:01+0000')
        output = list(filter.process([('run-2', run_2), ('run-3', run_3)]))
        assert output == [('run-3', run_3)]


class TestOldestUnfinishedRun:
    def test_forwards_input(self):
        filter = archivist.OldestUnfinishedRun()
        input = [('run-1', run_1), ('run-4', run_4)]
        output = list(filter.process(input))
        assert input == output

    def test_no_oldest_when_no_input(self):
        filter = archivist.OldestUnfinishedRun()
        filter.process([])
        assert filter.next_start() == None

    def test_when_only_finished_runs_it_says_first_is_oldest(self):
        filter = archivist.OldestUnfinishedRun()
        list(filter.process([('run-3', run_3)]))
        assert filter.next_start() == '2020-10-31T23:40:00+0000'

    def test_oldest_unfinished_runs(self):
        filter = archivist.OldestUnfinishedRun()
        list(filter.process([('run-1', run_1), ('run-4', run_4)]))
        assert filter.next_start() == '2020-10-31T23:39:00+0000'

    def test_remembers_oldest_from_previous_runs(self):
        filter = archivist.OldestUnfinishedRun()
        list(filter.process([('run-3', run_3)]))
        list(filter.process([]))
        assert filter.next_start() == '2020-10-31T23:40:00+0000'


@pytest.fixture()
def striv_with_runs(striv):
    striv.get('/runs', json={'run-1': run_1, 'run-2': run_2, 'run-3': run_3})
    striv.get('/run/run-2/logs', json={})
    striv.get('/run/run-3/logs', json={})


@pytest.fixture()
def start():
    return '2020-10-31T23:40:00+0000'


@pytest.fixture()
def unique_filter():
    return archivist.UniqueFinishedRuns()


@pytest.fixture()
def remember_oldest():
    return archivist.OldestUnfinishedRun()


@pytest.mark.usefixtures('striv_with_runs')
class TestRunOnce:
    def test_requests_logs_for_done_runs(self, striv, start, unique_filter, remember_oldest):
        archivist.run_once(start, unique_filter,
                           remember_oldest, 'http://localhost')
        assert [
            'http://localhost/runs?lower=2020-10-31T23:40:00+0000',
            'http://localhost/run/run-2/logs',
            'http://localhost/run/run-3/logs'
        ] == [r.url for r in striv.request_history]

    def test_prunes_finished_runs(self, start, unique_filter, remember_oldest):
        archivist.run_once(start, unique_filter,
                           remember_oldest, 'http://localhost')
        assert len(unique_filter.seen_runs) == 0

    def test_returns_new_start(self, start, unique_filter, remember_oldest):
        new_start = archivist.run_once(start, unique_filter,
                                       remember_oldest, 'http://localhost')
        assert new_start == '2020-10-31T23:40:02+0000'
